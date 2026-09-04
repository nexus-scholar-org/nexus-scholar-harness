---
workspace_id: SCI-001096
doi: 10.3390/agriengineering8010018
title: 'Deep Learning for Semantic Segmentation in Crops: Generalization from Opuntia
  spp.'
authors:
- family_name: Duarte-Rangel
  given_name: Arturo
  orcid: null
- family_name: Camacho-Bello
  given_name: C.
  orcid: null
- family_name: "Cornejo-Vel\xE1zquez"
  given_name: Eduardo
  orcid: null
- family_name: Clavel-Maqueda
  given_name: Mireya
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:00.689292+00:00'
---

# Deep Learning for Semantic Segmentation in Crops: Generalization from Opuntia spp.

Article Deep Learning for Semantic Segmentation in Crops: Generalization from Opuntia spp.

Arturo Duarte-Rangel 1, César Camacho-Bello 1,* , Eduardo Cornejo-Velazquez 2 and Mireya Clavel-Maqueda 2

1 Artificial Intelligence Laboratory, Universidad Politécnica de Tulancingo, Huapalcalco, Tulancingo 43629, Hidalgo, Mexico; arturo.duarte1931041@upt.edu.mx 2 Research Center on Technology of Information and Systems, Universidad Autónoma del Estado de Hidalgo, Mineral de la Reforma 42184, Hidalgo, Mexico; ecornejo@uaeh.edu.mx (E.C.-V.); mclavel@uaeh.edu.mx (M.C.-M.) * Correspondence: cesar.camacho@upt.edu.mx


## Abstract

Semantic segmentation of UAV–acquired RGB orthomosaics is a key component for quan- tifying vegetation cover and monitoring phenology in precision agriculture. This study evaluates a representative set of CNN–based architectures (U–Net, U–Net Xception–Style, SegNet, DeepLabV3+) and Transformer–based models (Swin–UNet/Swin–Transformer, SegFormer, and Mask2Former) under a unified and reproducible protocol. We propose a transfer–and–consolidation workflow whose performance is assessed not only through region–overlap and pixel–wise discrepancy metrics, but also via boundary–sensitive cri- teria that are explicitly linked to orthomosaic–scale vegetation–cover estimation by pixel counting under GSD (Ground Sample Distance) control. The experimental design considers a transfer scenario between morphologically related crops: initial training on Opuntia spp. (prickly pear), direct (“zero–shot”) inference on Agave salmiana, fine–tuning using only 6.84% of the agave tessellated set as limited target–domain supervision, and a subsequent consolidation stage to obtain a multi–species model. The evaluation integrates IoU, Dice, RMSE, pixel accuracy, and computational cost (time per image), and additionally reports the BF score and HD95 to characterize contour fidelity, which is critical when area is derived from orthomosaic–scale masks. Results show that Transformer-based approaches tend to provide higher stability and improved boundary delineation on Opuntia spp., whereas transfer to Agave salmiana exhibits selective degradation that is mitigated through low– annotation–cost fine-tuning. On Opuntia spp., Mask2Former achieves the best test perfor- mance (IoU 0.897 +/−0.094; RMSE 0.146 +/−0.002) and, after consolidation, sustains the highest overlap on both crops (IoU 0.894 +/−0.004 on Opuntia and IoU 0.760 +/−0.046 on Agave), while preserving high contour fidelity (BF score 0.962 +/−0.102/0.877 +/−0.153; HD95 2.189 +/−3.447 px/8.458 +/−16.667 px for Opuntia/Agave), supporting its use for final vegetation–cover quantification. Overall, the study provides practical guidelines for architecture selection under hardware constraints, a reproducible transfer protocol, and an orthomosaic–oriented implementation that facilitates integration into agronomic and remote–sensing workflows.

Academic Editor: Ray E. Sheriff

Received: 20 November 2025

Revised: 18 December 2025

Accepted: 22 December 2025

Keywords: semantic segmentation; UAV; RGB orthomosaics; precision agriculture; Opuntia spp.; Agave salmiana; U–Net; DeepLabV3+; SegFormer; swin–transformer; Mask2Former; transfer between domains; multi–species consolidation

Published: 5 January 2026

Copyright: © 2026 by the authors.

Licensee MDPI, Basel, Switzerland.

This article is an open access article

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license.

AgriEngineering 2026, 8, 18 https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 2 of 28


## 1. Introduction

The digital transformation of agriculture seeks to optimize production by integrating advanced technologies in crop management. The United Nations Sustainable Development Goals (SDGs), particularly SDG 2 (Zero Hunger), underscore the need for sustainable and efficient agricultural practices to ensure food security [1]. Precision agriculture (PA) has become a promising approach for increasing the efficiency and sustainability of crops through site–specific management, cost reduction and input minimization [2].

Based on observation and site–specific action, PA relies on remote sensing platforms such as satellites, manned aircraft, and unmanned aerial vehicles (UAVs) that allow the condition of the vegetation in each plot to be quantified at high resolution [3]. In particular, drones have become widespread due to their flexibility, low operating cost, and high spatial resolution, facilitating detailed monitoring of indicators such as vigor, water content, and plant density [4,5].

Previous studies have demonstrated the value of integrating UAV images with com- puter vision techniques to map crop health at different phenological stages [6], which has enabled new opportunities to estimate leaf areas, detect water stress, pests, or diseases, and even predict yields with greater timeliness and precision than traditional methods [7]. The current challenge is to develop general, robust image analysis algorithms for multiple crop types to scale PA beyond species-specific solutions.

In this context, Mexico has emblematic crops whose management systems could benefit from automated multi–crop monitoring. One of them is the prickly pear (Opuntia spp.), a perennial cactus of food and industrial importance. In 2022, about 12,491 ha of prickly pear were cultivated, with a production of 872 kt and a value of 2981 M MXN; 7.4 % of that production was exported, reflecting its economic relevance [8,9]. This crop stands out for its resistance to arid conditions and its versatility in uses (vegetable, forage, cosmetics, bioenergy), being a traditional component of Mexican agriculture [10]. Additionally, in states such as Hidalgo, prickly pear coexists with other semi–arid crops of value, such as the pulque agave (Agave salmiana), used to produce aguamiel and pulque. Hidalgo is the principal national producer of pulque agave (5079 ha) and ranks among the top producers of prickly pear fruit and tuna fruit [11]. Due to its climatic adaptation, Opuntia is regarded as a resilient crop under water-stress scenarios associated with climate change; however, maximizing sustainable productivity requires precise and repeatable plot-scale monitoring [12].

In UAV RGB orthomosaics, Opuntia and Agave share semi-arid imaging conditions (exposed soil, pronounced shadows, textured and heterogeneous backgrounds), yet they differ in plant geometry (cladodes vs. rosettes), occlusion patterns, and boundary character- istics; this combination defines a demanding setting to evaluate cross-domain transfer. The agronomic and socioeconomic relevance of both species is widely documented, both for their role in productive diversification in arid regions and for the associated value chains in food, fiber, and bioenergy [13,14].

Despite advances in agricultural computer vision, a significant gap persists: most segmentation models trained for a specific crop or condition tend to degrade their per- formance when applied to different scenarios without recalibration [15,16]. In general, this is due to variations among crops (morphology, color, texture) and among fields (light- ing, background, phenology) that alter the pixel distribution in the images. Traditional CNN–based algorithms efficiently learn features from the training set but tend to overfit; as a consequence, their generalization ability is limited. This need to re–label data for each new situation constitutes a bottleneck for practical applications. Various authors have em- phasized that the scarcity of annotated data and the intrinsic variability of agricultural con- ditions make it difficult to create universal segmenters [17]. Operationally, out-of-domain

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 3 of 28

degradation typically manifests as vegetation fragmentation, confusion with soil/shadows, and loss of contour continuity, which limits model reuse across fields and species without intensive retraining. Moreover, due to the common class imbalance between vegetation and soil, global metrics can artificially inflate the apparent model quality; therefore, the evalua- tion is grounded on overlap measures and boundary-sensitive criteria (Dice/F1, BF score, and HD95), which jointly quantify spatial agreement and geometric boundary deviation relative to the manual references. Under this definition, “stability” denotes lower sensi- tivity of the segmenter to variations in illumination, background, and morphology (i.e., reduced degradation under domain shift), whereas “boundary delineation” denotes higher geometric fidelity of contours (higher BF score and lower HD95).

In the case of prickly pear, until recently, there were virtually no publicly available datasets or research dedicated to its automatic segmentation. An initial advance was the work of Duarte–Rangel et al., who binarily segmented vegetation of Opuntia spp. in UAV orthomosaics using U–Net, DeepLabV3+, and U–Net Xception, achieving IoU val- ues of 0.66–0.67 to identify the vegetation area [18]. In parallel, Gutiérrez–Lazcano et al. demonstrated the usefulness of a U–Net Xception–Style model to detect the weed Cuscuta spp. in RGB orthomosaics captured with UAV [19]. However, both studies are limited to CNN–based architectures and do not address knowledge transfer to other crops, leaving open the need to explore approaches with greater generalization capacity. Patch-based pro- cessing facilitates training on large orthomosaics while preserving local detail (boundaries and soil–vegetation transitions). In contrast, orthomosaic–scale inference and reconstruc- tion recover spatial continuity in the final output.

On the other hand, Vision Transformers have revolutionized general computer vision by modeling global dependencies through self–attention [20]. In principle, this ability to capture context could lead to more robust segmentation under spatial and textural variations. Recent agricultural studies report competitive results for weed and crop seg- mentation with Transformer or hybrid CNN–Transformer designs [21–23]. Therefore, the balance between CNN/Transformer architectures in agriculture, and their ability to transfer knowledge with minimal recalibration, remains an open questions that motivate the present study. Recent agricultural literature supports the potential of self-attention for crop/weed segmentation with SegFormer-like models, as well as for multi-source inte- gration schemes that combine remote-sensing observations with meteorological variables, and even for spectral–spatial attention designs; collectively, these results suggest that Trans- formers can provide stronger contextual robustness under typical field variability [24–26]. However, for the comparison to be methodologically sound and actionable for adoption, it is also necessary to account for data requirements, memory footprint, and sensitivity to image resolution and partitioning, as these factors directly determine operational feasibility. In this study, hardware constraints are primarily framed in terms of GPU memory, training and inference time, and deployment feasibility within precision-agriculture workflows under limited computational resources.

This study focuses on quantifying, under a unified experimental framework, the gen- eralization and transfer capability of CNN- and Transformer-based architectures between Opuntia spp. and Agave salmiana, and on developing and validating a consolidated multi- species model that simultaneously preserves accuracy and boundary fidelity with min- imal recalibration. To foster adoption and reproducibility, we release the annotated dataset, code, and experimental artifacts (including hyperparameter tables and config- uration details), and we formalize an evaluation cycle to reduce the need for re-labeling when transferring models across species and field scenarios. To support these goals with comparable evidence, we jointly report overlap metrics, boundary-sensitive criteria, and computational-efficiency measures.

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 4 of 28

The following sections describe the study area and the capture of RGB orthomo- saics using a UAV; the dataset and its pixel-level annotation; and the unified experimen- tal framework (architectures and metrics). They also formalize the multicrop evalua- tion cycle, present an orthomosaic-scale pipeline with leaf area quantification, report a precision–efficiency benchmark, document reproducibility artifacts, and conclude with adoption guidelines.


## 2. Materials and Methods

2.1. Study Area 2.1.1. Study Area A—Opuntia spp., Tulancingo

The study area corresponds to an experimental prickly pear (Opuntia spp.) plot located in the Tulancingo Valley, Hidalgo, Mexico, georeferenced at 20.12555◦N and −98.37867◦W, a short distance from the Universidad Politécnica de Tulancingo (Figure 1). The unit was delimited at approximately 539 m2 to have a representative sample that allows an assessment of the acquisition and processing stages at the orthomosaic scale; the site selection obeys criteria of accessibility and proximity that optimize field logistics and the detailed characterization of agroecosystem components.


> **Figure 1. Geographic location of the study areas.**

2.1.2. Study Area B—Agave salmiana, Rancho La Gaspareña, Singuilucan

The second experimental site is located at Rancho La Gaspareña, at geographic co- ordinates 19.9692◦latitude and −98.5052◦longitude, in the community of Tlacoticpa, municipality of Singuilucan, Hidalgo, Mexico. The ranch is located at an average altitude of 2490 m a.s.l. on the eastern slope of the Sierra de Pachuca (Figure 1) and maintains approximately 15 ha of Agave salmiana (varieties “manso” and “chalqueño”) under rainfed conditions [27,28].

The radial arrangement of agave leaves provides an ideal setting for evaluating the transferability of segmentation models. Unlike the flat pads of Opuntia spp., agave exhibits more complex textural and geometric signatures, such as concentric patterns, cross shadows, and chromatic variations. These morphological differences, rather than being an obstacle, confer shape-, color-, and texture-based features that reinforce the model’s robustness,

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 5 of 28

as shown in Figure 2. For this reason, Rancho La Gaspareña represents an ideal case to test the capacity for cross–crop generalization, allowing us to assess how much of the representation learned in prickly pear is preserved when facing succulents with a different habit under equivalent climatic and edaphic conditions.


> **Figure 2. Contrasting leaf textures: flat pad of Opuntia spp. (A) versus radial leaf of Agave salmiana (B).**

2.2. Data Acquisition

The orthomosaic of Opuntia spp. was obtained using a DJI Mavic 2 Mini (DJI, Shenzhen, China) by planning the mission in Dronelink (Dronelink, Austin, TX, USA) at a height of 4 m. The flight plan combined three camera orientations and ensured 75% forward overlap and 70% lateral overlap, generating 443 RGB photographs at a resolution of 12 MP. Processing in WebODM (v2.8.4) yielded an average GSD (Ground Sample Distance) of 1.02 cm per pixel, corresponding to approximately 72 image pixels per cladode within the orthomosaic.

To compare with Agave salmiana and match the information density achieved in the prickly pear orthomosaic of an average of 72 pixels per cladode, the flight height was calculated from the linear relationship between ground distance and pixel size: since each agave leaf covers an area about six times larger, 61 m reproduces, on average, the number of pixels per leaf organ. This adjustment standardizes the geometric scale between crops, reduces the number of images, and shortens processing time without compromising the definition of contours and textures.

The mission was conducted at 11:00 h, replicating the prickly pear study’s solar window to ensure uniform illumination, minimize shadows, and maintain radiometric coherence across images. With 85% forward overlap and 80% lateral overlap, the flight covered 1 km, captured 75 RGB photographs at 12 MP, and generated an orthomosaic with an average GSD of 1.8 cm/pixel, enabling comparison of the morphological patterns of both succulent species without scale-related bias. The two orthomosaics obtained are shown in Figure 3.

2.3. Dataset

Two independent datasets were constructed from the RGB orthomosaics of Opun- tia spp. and Agave salmiana. Details of each set are shown in Table 1. In both cases, black padding was first applied so that the dimensions were exact multiples and non– overlapping crops of 96 × 96 pixels were extracted. These were manually annotated with Labelme to generate binary masks. The 96 × 96 px tiling size was selected as a compromise between sufficient local context and computational efficiency: at the acquisition resolutions

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 6 of 28

(GSD ≈1.02 cm/px for Opuntia and 1.8 cm/px for Agave), each crop covers approximately ~0.98 m and ~1.73 m per side, respectively, which preserves soil–vegetation transitions,

shadows, and boundary fragments that are informative for binary segmentation. This choice is consistent with prior patch-based segmentation practices on UAV RGB orthomo- saics, where crops of this order have been reported to retain discriminative information for vegetation delineation [19]. To mitigate the loss of orthomosaic-scale context, the method- ological scheme operates through tiling: inference is performed per tile and predictions are reassembled into the original orthomosaic geometry, so the spatial continuity of the final product is recovered during reconstruction.


> **Figure 3. RGB orthomosaics obtained with UAV of Opuntia spp. (left) and Agave salmiana (right)**

> plots, used as a basis for segmentation and quantification of plant cover.

Augmentation was applied only to the Opuntia base set to increase apparent variability in the smaller dataset, whereas Agave was kept non-augmented to preserve its distribution as the target adaptation domain under limited labeling. Validation and test splits for both crops were kept non-augmented, and results are reported by phase (base training, direct inference, and consolidation) to enable cross-domain comparisons on non-augmented data.


> **Table 1.**

> Comparative characteristics of the datasets used for segmenting Opuntia spp.
and
Agave salmiana.

Characteristic Opuntia spp. Agave salmiana

Original crops 186 335

Data augmentation Horizontal/Vertical flips and rotations ±90◦/180◦ Not applied

Total images after

augmentation 549 335

Train/test/val split 411/83/55 234/68/33 Purpose Training from scratch Fine–tuning the model

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 7 of 28

The RGB crops and their masks were rescaled to 224 × 224 pixels, as this is the reference resolution used during the pretraining of most ImageNet–based backbones; maintaining this format avoids reconfiguring input layers and allows leveraging robust initial weights, reducing convergence time and the risk of overfitting. Rescaling was implemented using bi- linear interpolation for RGB images and nearest-neighbor interpolation for binary masks to preserve discrete labels and avoid class-mixing artifacts along boundaries. It also increases the relative prominence of leaf edges and textures, thereby improving the network’s ability to discriminate contours accurately.

Black padding was used exclusively to enforce orthomosaic dimensions as exact multiples of the cropping window and to enable regular tiling. For the masks, padded regions were consistently treated as background. To prevent bias or artifacts, tiles whose area originates from padding were excluded from the annotated training/evaluation set, and all metrics were computed only over valid (non-padded) orthomosaic regions. The datasets are publicly available in the repository https://github.com/ArturoDuarteR/ Semantic-Segmentation-in-Orthomosaics.git (accessed on 20 November 2025).

2.4. Semantic Segmentation Techniques

Semantic segmentation assigns a class to each pixel, producing label maps that sep- arate regions of interest from the background. In precision agriculture, it enables the automated delineation of cultivated areas and target plants in UAV imagery. Its deploy- ment is challenged by strong field variability (illumination changes, phenological stages, weeds) that can reduce robustness [15], as well as the high spatial resolution of UAV data, which increases training and inference costs.

Deep learning has become the dominant approach for vegetation segmentation. Fully Convolutional Networks (FCN) enabled end–to–end learning for dense prediction [29], and encoder–decoder designs such as U–Net and SegNet improved spatial delineation. U–Net uses skip connections to fuse encoder and decoder features and performs well even with limited data [30], whereas SegNet reuses pooling indices for a more memory– efficient decoder [31]. DeepLabV3+ further strengthened multiscale representation through atrous convolutions and ASPP, coupled with a lightweight decoder to refine bound- aries [32]. Efficiency–oriented variants such as U–Net Style Xception replace the encoder with depthwise–separable blocks, often improving Dice/IoU in heterogeneous UAV agri- cultural scenes [33].

Transformer–based segmentation models incorporate attention to capture long–range dependencies, but early ViT formulations are computationally expensive due to global attention over image patches [34]. More efficient hierarchical alternatives include Swin Transformer (shifted windows) [35], SegFormer (efficient backbone with a lightweight MLP decoder) [23], and Mask2Former, which predicts masks via queries in an attention–based decoder and unifies multiple segmentation paradigms [36].

Based on this landscape, seven representative architectures were selected for compari- son: U–Net, DeepLabV3+, U–Net Style Xception, SegNet, Swin-Transformer, SegFormer, and Mask2Former.

2.4.1. UNet

UNet adopts a U-shaped architecture composed of a symmetric encoder–decoder pair connected through a central bottleneck. Its defining element is the set of skip connec- tions between homologous stages, which preserves fine-grained spatial details and fuses them with higher-level semantic representations, enabling accurate pixel-wise segmen- tation even with limited training data (Figure 4). In the encoder, each stage applies two 3 × 3 convolutions with ReLU activation, followed by max-pooling to reduce spatial reso-

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 8 of 28

lution while increasing the number of feature channels; the decoder reverses this process via transposed convolutions and feature fusion with the corresponding skip–connections. This hierarchical design captures both contextual information and local boundaries without dense layers that would inflate the parameter count; consequently, UNet remains memory- efficient, end-to-end trainable, and less prone to overfitting when combined with intensive data augmentation [30].


> **Figure 4. UNet: encoder–decoder in a “U” shape with shortcuts that restore fine details.**

2.4.2. DeepLabV3+

DeepLabV3+ (Figure 5) is an encoder–decoder semantic segmentation architecture that couples atrous (dilated) convolutions with an Atrous Spatial Pyramid Pooling (ASPP) module to aggregate multi-scale context by sampling feature maps at multiple dilation rates while preserving spatial resolution; the encoder is commonly instantiated with an Xception backbone based on depth-wise separable convolutions to reduce parameters and computation without sacrificing representational power, and a lightweight decoder then upsamples the ASPP output and fuses it with low-level encoder features to restore fine spatial detail, yielding sharper boundary localization and improved delineation of irregular objects with marginal additional overhead, while remaining modular with respect to alternative backbones for accuracy–efficiency trade-offs [32].

2.4.3. UNet Style Xception

UNet Style Xception (Figure 6) preserves the UNet encoder–decoder topology with skip connections while replacing the conventional encoder with Xception en- try/middle/exit flows based on depth-wise separable convolutions and internal residual shortcuts, thereby reducing parameterization and improving semantic feature extraction; in this configuration, standard convolutional blocks are reformulated as depthwise–pointwise sequences that enhance gradient propagation and accelerate convergence, and the resulting latent representation can be complemented by a compact context module (e.g., reduced ASPP or channel–pixel attention) to expand the receptive field without degrading spa- tial resolution, after which the decoder upsamples and concatenates low-level features to recover acceptable boundaries through additional separable convolutions, achieving improved pixel-wise delineation at lower computational cost, consistent with the Dice gains reported by Moodi et al. [37].

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 9 of 28


> **Figure 5. DeepLabV3+ overview. The encoder (left) extracts multi-scale features using atrous**

> convolutions and projects them with a 1 × 1 layer. The decoder (right) fuses high-level features with
low-level features via a skip connection (horizontal arrow) and a Concat operation, then restores
spatial resolution through Upsample ×4 steps before a 3 × 3 convolution and the final prediction.
Arrows indicate data flow, and colors (orange/blue/green) denote different feature levels (high-level,
intermediate, and low-level, respectively).


> **Figure 6. U–Net Style Xception: efficient separable Xception encoder with lateral bridges.**

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 10 of 28

2.4.4. SegNet

SegNet is a fully convolutional encoder–decoder architecture in which the encoder follows the VGG–16 convolutional stages with ReLU activations and max-pooling, while the decoder performs non-linear upsampling by unpooling using the stored max-pooling indices, thereby reconstructing sparse high-resolution feature maps without learning decon- volution kernels (Figure 7). Each unpooling step is followed by convolutional refinement to recover spatial structure, progressively restoring the original resolution, and the network terminates with a pixel-wise classifier (e.g., binary or multi-class) applied to the restored feature maps. By reusing pooling switches, SegNet reduces memory footprint and compu- tational overhead relative to decoders that require learned upsampling, while maintaining competitive boundary localization through index-guided spatial reconstruction [31].


> **Figure 7. Simplified scheme of SegNet (left: input image; center: convolutional encoding and**

> decoding; right: segmented mask). The blue bars (convolution+ReLU) extract features, the green
bars (pooling) reduce resolution, and the red bars (upsampling) use max–pooling indices to resample.
The final yellow layer assigns a class to each pixel.

2.4.5. Swin–Transformer

Swin–Transformer is a hierarchical vision Transformer that constructs multi-scale fea- ture representations via window-based self-attention, enabling efficient modeling of spatial dependencies in scenes with substantial scale variability. Self-attention is computed within non-overlapping local windows to control complexity, while the shifted-window scheme alternates the window partitioning across consecutive layers to promote cross-window information exchange and approximate global context without the quadratic cost of dense attention. The backbone is organized into four pyramid stages: the image is first embed- ded into fixed-size patch tokens; successive Swin blocks perform intra-window attention; and patch-merging operations downsample the spatial grid while increasing the channel dimensionality, yielding progressively more abstract features (Figure 8). For semantic seg- mentation, this backbone is typically integrated into an encoder–decoder design in which the encoder supplies multi-resolution representations and a symmetric decoder performs patch-expanding upsampling and fuses corresponding stages through skip connections (UNet-like) to restore full resolution and produce dense pixel-wise predictions [35].

2.4.6. SegFormer

SegFormer is an efficient Transformer-based semantic segmentation architecture that couples a hierarchical Mix Transformer (MiT) encoder with a lightweight all-MLP decoder to achieve strong accuracy under constrained computation. The MiT backbone produces multi-scale feature maps via stage-wise token representations and efficient self-attention mechanisms that capture long-range dependencies without the prohibitive cost of early ViT designs, while normalization and pointwise (1 × 1) projections facilitate stable fea- ture mixing across channels. Instead of employing computationally intensive context

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 11 of 28

modules (e.g., ASPP) or heavy convolutional decoders, SegFormer uses linear projections to align channel dimensions and fuses the multi-resolution features with minimal over- head, yielding a compact segmentation head that is memory-efficient and fast at inference (Figure 9). This encoder–decoder formulation provides a favorable accuracy–efficiency trade-off for high-resolution semantic segmentation where throughput and resource usage are critical [23].


> **Figure 8. Scheme of the Swin Transformer for binary segmentation in agricultural images; (a) Hierar-**

> chical representation: the image is divided into patches and processed at multiple scales; (b) Shifted
windows: self–attention is calculated in local windows and, by shifting them, captures inter–window
context; (c) Successive blocks: each stage alternates W–MSA/SW–MSA with normalization (LN) and
residual MLP; and (d) Architecture in four stages with progressive patch merging that produces a
binary prediction map at the end of the pipeline.


> **Figure 9. SegFormer architecture with hierarchical encoder and lightweight MLP–based decoder to**

> generate the segmentation map.

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 12 of 28

2.4.7. Mask2Former

Mask2Former formulates segmentation as a set prediction problem in which a fixed number of learnable queries jointly infer class labels and dense masks, enabling a single architecture to support semantic, instance, and panoptic outputs. Its central contribution is masked cross-attention: at each decoder layer, the attention logits between queries and spatial tokens are multiplicatively gated by a query-specific binary/soft mask, restrict- ing information flow to the predicted region and enforcing region-conditioned feature aggregation. This coupling reduces spurious context mixing, strengthens the separation of disconnected regions, and yields sharper boundary localization than unconstrained global attention decoders. In practice (Figure 10), multi-scale features from a backbone such as Swin Transformer are fused within a transformer decoder that iteratively refines queries and masks across pyramid levels, producing coarse-to-fine mask updates and improving scale robustness while keeping computation focused on candidate regions [36].


> **Figure 10. Architecture of Mask2Former, which combines a backbone and a pixel decoder with an**

> iterative Transformer decoder based on masked attention to predict classes and segmentation masks.

2.5. Knowledge Transfer

Transfer learning (TL) involves reusing knowledge captured by a previously trained model, typically trained on a broad domain or related tasks, to accelerate convergence and improve generalization in a new scenario with scarce data. Operationally, the most widespread procedure in computer vision is to initialize the weights of the first layers with parameters learned in an abundant set and fine–tune the last layers on the target task (Figure 11). This strategy preserves generic such as edges and textures, thereby focusing specific learning on a reduced subset of parameters and reducing both overfitting and computational.

The usefulness of TL is twofold: on the one hand it alleviates the chronic lack of labeled data, caused by the difficulty of annotating large orthomosaics and the need for experts to validate the classes, and on the other it facilitates adaptation between related domains, for example from one crop to another where plant morphology and lighting conditions differ but share formal color and texture patterns. A recent review quantifies that more than 60% of agricultural studies using Deep Learning already employ some TL scheme, highlighting its role in overcoming labeling and hardware bottlenecks [38].

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 13 of 28


> **Figure 11. Illustration of knowledge transfer between crops: a base model pretrained with the Opuntia**

> spp. dataset transfers its weights and representations to perform fine–tuning with a reduced Agave
salmiana dataset, generating a consolidated model.

2.6. Evaluation of Metrics

The experiments were quantitatively evaluated using metrics computed from pre- dicted and reference binary masks, where 1 denotes vegetation pixels and 0 denotes back- ground pixels. Spatial agreement was measured using Intersection over Union (IoU) and the Dice coefficient; global correctness with pixel accuracy; and overall discrepancy with the Root Mean Squared Error (RMSE). Because this study emphasizes boundary delineation, contour quality was additionally evaluated using the Boundary F1 (BF score) and the 95th- percentile Hausdorff distance (HD95) to capture boundary alignment and near-worst-case.

• Intersection over Union (IoU). The Intersection over Union (IoU), also known as the Jaccard Index, quantifies the overlap between the predicted mask Mp and the reference mask Mr:

IoU = |Mp ∩Mr|

|Mp ∪Mr|, (1)

where | · | denotes the number of pixels in the corresponding set. The metric ranges from 0 (no overlap) to 1 (perfect match) and penalizes both false negatives and false positives, reflecting spatial agreement of vegetation extent. • Dice coefficient. The Dice coefficient measures region overlap with increased sensitivity to agreement in the positive class:

Dice = 2 |Mp ∩Mr|

|Mp| + |Mr|, (2)

where |Mp| and |Mr| are the number of predicted and reference vegetation pixels, respectively. Dice’s coefficient ranges from 0 to 1, with higher values indicating greater agreement. • Pixel accuracy. Pixel accuracy reports the fraction of correctly classified pixels over the full image:

Acc = TP + TN TP + TN + FP + FN, (3)

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 14 of 28

where TP, TN, FP and FN denote true positives, true negatives, false positives and false negatives, respectively. Although it can be inflated under class imbalance, it is included as a standard global reference. • Root Mean Squared Error (RMSE). The Root Mean Squared Error (RMSE) measures the average discrepancy between predicted probabilities ˆyi ∈[0, 1] (or binary predictions) and binary labels yi ∈{0, 1} over all N pixels:

v u u t 1

N ∑ i=1

( ˆyi −yi)2, (4)

RMSE =

N

where lower values indicate predictions closer to the correct extremes (0 or 1), which is relevant for reliable vegetation cover estimation. • Boundary F1 (BF score). The Boundary F1 (BF score) evaluates contour alignment by comparing boundary pixel sets

Bp and Br (extracted from Mp and Mr) under a tolerance δ. Let d(x, B) = minb∈B ∥x −b∥2. Boundary precision and recall are computed as

Pb = |{x ∈Bp : d(x, Br) ≤δ}|

|Bp| , Rb = |{x ∈Br : d(x, Bp) ≤δ}|

|Br| , (5)

and combined into

BF = 2 Pb Rb Pb + Rb

. (6)

This metric emphasizes boundary localization quality while allowing small spatial tolerances. • 95th-percentile Hausdorff distance (HD95). HD95 measures near-worst-case boundary deviation while reducing sensitivity to isolated outliers. Using boundary sets Bp and Br, define point-to-set distances d(x, B) = minb∈B ∥x −b∥2. Then





perc95{d(x, Br) : x ∈Bp}, perc95{d(y, Bp) : y ∈Br}

HD95 = max

, (7)

where perc95{·} denotes the 95th percentile. HD95 is reported in pixels.


## 3. Methodology

3.1. Implementation Details

All experiments were carried out on a workstation based on Pop! OS 22.04 LTS, equipped with a 12th generation Intel Core i9–12900K processor (24 threads, up to 5.2 GHz), 32 GB of RAM and an NVIDIA GeForce RTX 4060 Ti GPU with 16 GB GDDR6 memory. The operating system runs on Linux kernel 6.12.10, with CUDA 12.8 support and NVIDIA driver 570.153.02. The station has an x86–64 architecture and was manufactured by Micro– Star International (model MS–7E06). The experiments were conducted in PyCharm using Python 3.10, with PyTorch 2.6.0 and TorchVision 0.21.0 as the primary frameworks. Aux- iliary libraries: NumPy (v2.2.6), OpenCV–Python (v4.11.0), and Matplotlib(v3.10.3) were used only for image preprocessing, metric instrumentation, and result visualization.

3.2. Specific Configuration of the Models

All experiments were performed in a binary segmentation setting (NUM_CLASSES = 1) using 224 × 224 image patches. Data loading was configured with model-dependent batch sizes (4–16) and parallel workers (8–16), while maintaining consistent preprocessing across splits. Data augmentation was primarily geometric (random horizontal/vertical flips with

p = 0.5 and rotations implemented as ±15◦perturbations or discrete 90◦steps), comple-

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 15 of 28

mented in some configurations by mild photometric jitter (brightness/contrast or ColorJitter) to increase appearance variability without altering the target mask definition.

To compare architectures under controlled conditions, an everyday three-stage sched- ule was adopted for all seven models: base training (150 epochs), fine-tuning (30 epochs), and consolidation (10 epochs). Learning rates were stage-wise, typically 1 × 10−4 for base/fine-tuning and 1 × 10−5 for consolidation, with model-specific adjustments (e.g., U-Net Xception-Style used 3 × 10−4 in base training and 2 × 10−5 in consolidation, and in- cluded ReduceLROnPlateau and early stopping). Most models were optimized with AdamW, whereas Swin-UNet used Adam; weight decay was set according to each architec- ture’s configuration.

Loss functions were defined according to the binary output: U-Net and DeepLabV3+ employed BCEWithLogitsLoss with positive-class weighting (pos_w = 3.0) combined with a Dice term, SegNet used BCE, and Swin-UNet/SegFormer/Mask2Former used BCEWith- LogitsLoss + 0.5 DiceLoss. Fine-tuning was implemented via partial freezing, training only the task-critical blocks (e.g., decoder/head and late backbone stages) while keeping early encoder/backbone layers fixed; consolidation re-opened all layers for joint optimization at the reduced learning rate. A default probability threshold of 0.5 was used in the base phase; during transfer, U-Net and DeepLabV3+ used a fixed threshold of 0.35, while Seg- Former and Mask2Former used a validation-driven sweep in the range 0.30–0.70. Details of the hyperparameter configuration used in this study are summarized in Table 2. Full per-model tables (including all stage-wise hyperparameters) are available in the reposi- tory at https://github.com/ArturoDuarteR/Semantic-Segmentation-in-Orthomosaics.git (accessed on 20 November 2025).


> **Table 2.**

> General hyperparameter summary per model.
The stage schedule was fixed to
T/FT/C = 150/30/10 epochs, where T denotes base training, FT denotes fine-tuning, and C
denotes consolidation.

Model Batch Opt. LR WD Loss Thr. Fine-Tuning (Trainable; Frozen)

Swin–Transformer 4 Adam T/FT: 1 × 10−4

0.5 Head + Stage 3 (freeze Stages 0–2)

C: 1 × 10−5 0 BCELogits

+0.5Dice

SegNet 16 AdamW T/FT: 1 × 10−4

C: 1 × 10−5 1 × 10−5 BCE 0.5 enc4–enc5 + decoder (freeze enc1–enc3)

T: 3 × 10−4

T: 1 × 10−4

0.5 e4–bottleneck + decoders (freeze e1–e3)

FT/C: 1 × 10−5 T: BCELogits+0.5Dice

FT: 1 × 10−4

UNet–Style–Xception 6 AdamW

FT/C: BCELogits

C: 2 × 10−5

DeepLabV3+ 8 AdamW T/FT: 1 × 10−4

T: 0.5 FT/C: 0.35

Head + backbone.layer4 (freeze layer 0–3)

C: 1 × 10−5 1 × 10−5 BCELogits(pos_w = 3)

+ (1-Dice)

U–Net 8 AdamW T/FT: 1 × 10−4

T: 0.5 FT/C: 0.35

Bottleneck + decoder + output (freeze enc1–enc4)

C: 1 × 10−5 1 × 10−5 BCELogits(pos_w = 3)

+ (1-Dice)

T: 0.5 FT/C: sweep

T: 1 × 10−2

SegFormer 4 AdamW T/FT: 1 × 10−4

decode_head (freeze encoder)

FT/C: 1 × 10−4 BCELogits

C: 1 × 10−5

+0.5Dice

0.30–0.70

T: 0.5 FT/C: sweep

T: 1 × 10−2

Mask2Former 4 AdamW T/FT: 1 × 10−4

Decoder + heads (freeze backbone + pixel_decoder)

FT/C: 1 × 10−4 BCELogits

C: 1 × 10−5

+0.5Dice

0.30–0.70

3.3. Methodological Workflow for Orthomosaic Processing, Model Training, and Vegetation Cover Estimation

The workflow was structured into five sequential phases (Figure 12) that integrate or- thomosaic generation, tile-based dataset construction and annotation, and supervised train- ing of CNN- and Transformer-based segmenters, complemented by a knowledge-transfer and consolidation scheme to analyze cross-crop generalization. This methodological design culminates in quantifying vegetation cover at the orthomosaic scale to derive an agronomic indicator from the segmented masks, while preserving consistency across spatial prediction, inter-domain adaptation, and the final estimation of the agronomic parameter.

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 16 of 28


> **Figure 12. Proposed methodological flow: (1) generation of RGB orthomosaics via photogrammetry,**

> (2) tessellation, scaling and data augmentation, (3) binary annotation in LabelMe, (4) training and
validation of CNN and Transformer segmenters with direct inference on agave and fine–tuning,
and (5) consolidation of the model to estimate plant cover in orthomosaics as an agronomic indicator.

1. Image capture and orthorectification: The RGB acquisition procedure followed the photogrammetric protocol described by Duarte–Rangel et al. [18]. Flights were planned with adequate longitudinal and lateral overlap using a lightweight mul- tirotor UAV to ensure redundancy for accurate reconstruction. Images were processed in WebODM to generate georeferenced orthomosaics that preserve plot geometry and enable subsequent spatially consistent tessellation. 2. Preprocessing and dataset enrichment: Before tessellation, black padding was applied to enforce orthomosaic dimensions as exact multiples of the tessellation window. The orthomosaic was then decomposed into non–overlapping tiles (96 × 96 px), dis- carding patches with negligible vegetation to reduce trivial samples. The selected tiles were augmented using moderate geometric transforms (random flips and dis- crete rotations) and rescaled to 224 × 224 px to ensure compatibility with pretrained backbones and to standardize the network input across architectures. 3. Vegetation cover annotation: Tiles were imported into LabelMe for manual delineation of two semantic categories (plant and background), producing binary ground-truth masks used for supervised optimization and objective evaluation. 4. Training, validation, and segmentation: The dataset was partitioned into training, validation, and testing subsets. Models from convolutional encoder–decoder families and Transformer-based designs were trained under a unified training protocol defined as a fixed three-stage schedule: base training on Opuntia (T), fine-tuning on Agave (FT) with partial freezing of early encoder/backbone blocks, and a short consolidation stage (C) with all layers unfrozen at a reduced learning rate for joint optimization. Model performance was quantified using IoU, RMSE, and pixel accuracy, and com- plemented with Dice, BF score, and HD95 to explicitly characterize region overlap and boundary fidelity; the mean inference time per tile was also recorded. 5. Cross–crop transfer, consolidation, and vegetation cover estimation: To assess gen- eralization, models trained on Opuntia spp. were first applied directly to the Agave salmiana orthomosaic (direct inference). Subsequently, fine-tuning was conducted

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 17 of 28

using 6.84% of the Agave orthomosaic tiles (image patches) to adapt the model with limited target-domain supervision, followed by consolidation on the combined (Op- untia+Agave) data. Finally, vegetation cover (leaf area) was estimated from the re- constructed orthomosaic-scale binary masks via pixel counting and GSD conversion, i.e., Aveg = Nveg · GSD2, where Nveg is the number of pixels predicted as vegetation and GSD is the ground sampling distance of the orthomosaic. The resulting estimates were compared against the manual reference to quantify agreement at the level of the agronomic indicator.


## 4. Results

This section presents empirical evidence supporting the robustness of the evaluated architectures in the proposed cross-crop setting. First, we establish a baseline by analyzing the performance of models trained on Opuntia spp. and evaluated on its test set. Next, we examine generalization to Agave salmiana through direct (zero-shot) inference and through light fine-tuning with limited target-domain supervision. We then assess the consolidated multi-species checkpoints obtained after a short joint optimization on mixed Opuntia+Agave data, using both region-overlap and boundary-focused metrics to characterize accuracy and contour fidelity. Finally, the consolidated predictions are translated into orthomosaic-scale plant-cover estimates via pixel counting under GSD control, enabling a direct comparison between manual and automatic quantification.

4.1. Performance of the Models Trained on Opuntia spp.


> **Table 3 reports the mean ± standard deviation across test tiles, enabling a joint as-**

> sessment of central tendency (accuracy) and dispersion (stability) for each architecture.
Under this criterion, Mask2Former achieved the highest mean IoU (0.897), the lowest
RMSE (0.146), and the highest pixel accuracy (0.968), indicating the best overall agreement
with the reference masks while limiting systematic over- and under-segmentation. Im-
portantly, the improvement in mean IoU over the second-best model (Swin–Transformer,
0.885) is modest (∆IoU ≈0.012), whereas the reduction in RMSE is more pronounced
(0.167 →0.146), which is consistent with fewer probability/label mismatches concentrated
around transition regions (soil–vegetation boundaries). Inference times for Mask2Former
and Swin–Transformer are comparable (∼8–9 ms per tile), suggesting that the observed
accuracy differences are not driven by a strong speed–accuracy trade-off within this top-
performing group.

Beyond average performance, variability differs substantially between models: Swin– Transformer exhibits a larger IoU dispersion (±0.116) than Mask2Former (±0.094), suggest- ing higher sensitivity to tile-level heterogeneity (e.g., local illumination changes, mixed pixels, or background texture). SegFormer provides the fastest inference (∼0.7 ms per tile) but with a lower mean IoU (0.799), evidencing a throughput-oriented operating point that may be advantageous for large-scale mapping when minor losses in spatial agreement are acceptable. DeepLabV3+ attains competitive accuracy (IoU 0.788; pixel accuracy 0.934) but at a markedly higher computational cost (38.9 ms per tile), which can become limiting when processing full orthomosaics. Among CNN-based baselines, UNet–Style–Xception yields higher IoU than SegNet and U–Net (0.667 vs. 0.597 and 0.678, respectively) and remains relatively efficient (2.9 ms), supporting its role as a practical compromise; however, the overall ranking indicates that Transformer-based backbones/decoders better capture long-range context and preserve spatial consistency in this dataset, particularly under tile-level variability.

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 18 of 28


> **Table 3. Performance on the Opuntia spp. test set.**

Metric Swin– Transformer SegNet UNet–Style–

Xception DeepLabV3+ U–Net SegFormer Mask2Former

IoU 0.885 ± 0.116 0.597 ± 0.014 0.667 ± 0.008 0.788 ± 0.057 0.678 ± 0.038 0.799 ± 0.0001 0.897 ± 0.094 RMSE 0.167 ± 0.088 0.346 ± 0.006 0.285 ± 0.005 0.228 ± 0.039 0.290 ± 0.021 0.213 ± 0.0001 0.146 ± 0.002 Pixel accuracy 0.965 ± 0.044 0.869 ± 0.006 0.890 ± 0.004 0.934 ± 0.022 0.886 ± 0.016 0.937 ± 0.000 0.968 ± 0.001

timg (s) 0.0083 ± 0.0185 0.0060 ± 0.000006 0.0029 ± 0.000007 0.0389 ± 0.0075 0.0068 ± 0.0002 0.0007 ± 0.0000 0.0089 ± 0.0000

4.2. Knowledge Transfer to Agave (Fine–Tuning) 4.2.1. Direct Inference

Direct inference (i.e., zero-shot transfer) evaluates cross-crop generalization by apply- ing the models trained exclusively on Opuntia spp. to Agave salmiana without updating any weights; therefore, the results in Table 4 should be interpreted as a baseline under domain shift (differences in organ geometry, spatial arrangement, background texture, and scale). In this setting, several architectures tend to produce background-dominant predictions, which manifest as near-zero overlap with the reference masks (IoU close to zero) and indicate that the learned decision boundary does not readily translate to agave morphology. In particular, DeepLabV3+ yields an extreme case in which most pixels are assigned to the background class, consistent with a collapse to the majority class under a strong appearance mismatch rather than with a training instability, and highlighting limited out-of-domain transfer for this configuration.

In contrast, other models retain partial transfer capability without target-domain su- pervision. UNet–Style–Xception attains the highest mean IoU (0.664 ± 0.007) and pixel accuracy (0.913 ± 0.003), and its low dispersion suggests comparatively stable behavior across tiles, which is compatible with feature extraction that captures morphology-invariant cues (e.g., vegetation texture and boundary evidence) beyond the source crop. SegNet and U–Net also produce non-trivial segmentations, albeit with lower agreement, indicating that their convolutional representations partially extrapolate to the new geometry. Transformer- based models (Swin–Transformer, SegFormer, and Mask2Former) exhibit heterogeneous outcomes in this direct-transfer setting, as reflected by the reported variability and/or reduced agreement, suggesting higher sensitivity to the source–target shift when no adap- tation is performed. Overall, these observations motivate the subsequent fine-tuning stage as a controlled mechanism to realign the models to agave appearance while preserving the representations learned on Opuntia.


> **Table 4. Performance in direct inference on Agave salmiana of the models trained in Opuntia spp.**

Metric Swin– Transformer SegNet UNet–Style–

Xception DeepLabV3+ U–Net SegFormer Mask2Former

IoU 0.585 ± 0.126 0.628 ± 0.017 0.664 ± 0.007 0.000 ± 0.000 0.559 ± 0.079 0.541 ± 0.001 0.515 ± 0.015 RMSE 0.300 ± 0.132 0.286 ± 0.009 0.255 ± 0.005 0.449 ± 0.057 0.315 ± 0.027 0.325 ± 0.000 0.325 ± 0.009 Pixel accuracy 0.892 ± 0.092 0.907 ± 0.004 0.913 ± 0.003 0.795 ± 0.052 0.860 ± 0.016 0.873 ± 0.000 0.869 ± 0.008

timg (s) 0.0110 ± 0.0227 0.0109 ± 0.0040 0.0048 ± 0.00004 0.0579 ± 0.0531 0.0093 ± 0.0069 0.007 ± 0.000 0.029 ± 0.000

4.2.2. Fine–Tuning

To adapt the representations learned on Opuntia spp. to the radial morphology of Agave salmiana, fine-tuning was performed for 30 epochs using a reduced learning rate and partial freezing, as described in the Implementation details section. Specifically, the Agave salmiana orthomosaic was tessellated following the same methodological scheme defined for Opuntia, yielding a total of 4900 tiles. Subsequently, applying the same filtering and selection criterion for informative patches (excluding tiles with negligible vegetation), a

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 19 of 28

subset of 335 tiles was extracted to provide limited target-domain supervision. This subset comprises 6.84% of the total number of generated tiles. Table 5 summarizes the metrics obtained after this adaptation.


> **Table 5. Performance after fine–tuning on Agave salmiana.**

Metric Swin– Transformer SegNet UNet–Style–

Xception DeepLabV3+ U–Net SegFormer Mask2Former

IoU 0.741 ± 0.103 0.710 ± 0.012 0.685 ± 0.006 0.772 ± 0.049 0.746 ± 0.064 0.707 ± 0.000 0.754 ± 0.104 RMSE 0.212 ± 0.078 0.243 ± 0.011 0.231 ± 0.003 0.211 ± 0.013 0.209 ± 0.017 0.229 ± 0.001 0.208 ± 0.002 Pixel accuracy 0.949 ± 0.036 0.932 ± 0.003 0.925 ± 0.001 0.947 ± 0.007 0.938 ± 0.011 0.941 ± 0.000 0.951 ± 0.001 timg (s) 0.0070 ± 0.0010 0.0090 ± 0.0040 0.0030 ± 0.0001 0.0389 ± 0.0075 0.0069 ± 0.0002 0.004 ± 0.000 0.024 ± 0.000

Fine-tuning on Agave salmiana quantifies adaptation under limited target supervi- sion (30 epochs; 335 tiles, i.e., ≈6.84% of the agave tessellated set), and its effect can be interpreted relative to the direct-inference baseline by inspecting changes in overlap (IoU), discrepancy (RMSE), and variability (standard deviation) reported in Table 5. In this set- ting, DeepLabV3+ attains the highest mean IoU after adaptation, which is consistent with the capacity of its atrous multiscale representation to recover agave structures once the decision boundary is re-aligned to the target appearance; the contrast with its near-zero IoU under direct inference indicates that its failure mode is dominated by domain shift rather than by insufficient model capacity. Mask2Former, in turn, exhibits the lowest mean error (RMSE) and the highest pixel accuracy after fine-tuning, suggesting a more reliable pixel-level assignment when the model is exposed to agave examples; this behavior is consistent with query-based masked-attention decoding, which refines region predictions under target-domain cues. UNet–Style Xception and SegFormer remain competitive from a computational perspective. Yet, their post-adaptation scores indicate smaller gains in cap- turing the radial leaf arrangement, suggesting that their representations may require either more target samples or stronger boundary-aware supervision to close the gap. Overall, the fine-tuning results not only increase averages but also differentiate models by adapta- tion stability (dispersion across tiles) and by the balance between overlap improvement and error reduction, thereby providing a technical basis for selecting architectures based on accuracy requirements and orthomosaic-scale deployment constraints.

4.3. Intercropping Consolidation (Opuntia spp. + Agave salmiana)

After completing the consolidation stage (C), a single consolidated multi-species model was obtained for each architecture, i.e., one final checkpoint per model family. This phase consisted of 10 training epochs using a 1:1 mixture of prickly pear and agave images, with a uniform learning rate of 1 × 10−5 across all models. The goal was to preserve the knowledge previously acquired on prickly pear while simultaneously stabilizing performance on agave, thereby mitigating catastrophic forgetting and encouraging a shared representation across species. To assess the consolidated models, we report IoU, RMSE, pixel accuracy, and mean inference time, and additionally Dice, Boundary F1 (BF score), and HD95 to explicitly characterize region overlap and boundary fidelity. Crop-wise results are provided in Tables 6 and 7.

The intercropping consolidation phase allowed evaluating the ability of the models to operate jointly on both crops after a cross–crop adjustment. This assessment was performed using region-based metrics (IoU and Dice), global correctness (pixel accuracy), discrepancy (RMSE), and boundary-focused criteria (BF score and HD95) reported in Tables 6 and 7. In Opuntia spp., the best performance was achieved by Mask2Former, with the highest IoU and accuracy, as well as the lowest mean error. Consistently, it also achieved the highest Dice and BF score and the lowest HD95, indicating superior boundary fidelity in the consolidated

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 20 of 28

setting; moreover, its IoU variability is minimal (±0.004), suggesting stable behavior across tiles. These results suggest that attention-based decoders can integrate multi-species variability while preserving contour alignment, whereas several CNN/hybrid baselines exhibit weaker boundary localization (lower BF score and larger HD95) despite comparable coarse overlap in some cases. In contrast, UNet–Style–Xception and U–Net showed notably lower IoU and accuracy, indicating limited generalization capacity under multicrop scenarios. This limitation is further reflected in their boundary metrics (lower BF score and substantially higher HD95), which indicates larger contour deviations after consolidation.


> **Table 6. Performance on Opuntia spp. after intercropping consolidation.**

Metric Swin– Transformer SegNet UNet–Style–

Xception DeepLabV3+ U–Net SegFormer Mask2Former

IoU 0.879 ± 0.116 0.713 ± 0.046 0.625 ± 0.010 0.758 ± 0.053 0.660 ± 0.038 0.792 ± 0.000 0.894 ± 0.004 RMSE 0.172 ± 0.087 0.265 ± 0.025 0.293 ± 0.003 0.249 ± 0.037 0.293 ± 0.021 0.246 ± 0.001 0.155 ± 0.005 Pixel accuracy 0.963 ± 0.045 0.906 ± 0.021 0.878 ± 0.003 0.923 ± 0.022 0.876 ± 0.017 0.935 ± 0.000 0.967 ± 0.001 Dice 0.950 ± 0.035 0.736 ± 0.070 0.757 ± 0.068 0.900 ± 0.051 0.796 ± 0.050 0.902 ± 0.032 0.956 ± 0.036 BF score 0.952 ± 0.103 0.385 ± 0.059 0.429 ± 0.066 0.782 ± 0.153 0.425 ± 0.057 0.752 ± 0.083 0.962 ± 0.102 HD95 (px) 2.759 ± 3.391 22.624 ± 11.303 20.771 ± 10.419 7.947 ± 7.758 18.276 ± 6.764 8.724 ± 5.283 2.189 ± 3.447 timg (s) 0.0073 ± 0.0009 0.0086 ± 0.0035 0.0029 ± 0.0001 0.0398 ± 0.0050 0.0069 ± 0.0001 0.0042 ± 0.0001 0.0237 ± 0.0001


> **Table 7. Performance on Agave salmiana after intercropping consolidation.**

Metric Swin– Transformer SegNet UNet–Style–

Xception DeepLabV3+ U–Net SegFormer Mask2Former

IoU 0.738 ± 0.106 0.700 ± 0.010 0.719 ± 0.003 0.756 ± 0.055 0.721 ± 0.032 0.715 ± 0.000 0.760 ± 0.046 RMSE 0.212 ± 0.077 0.235 ± 0.006 0.217 ± 0.002 0.219 ± 0.029 0.226 ± 0.018 0.224 ± 0.001 0.208 ± 0.002 Pixel accuracy 0.949 ± 0.035 0.929 ± 0.004 0.933 ± 0.001 0.940 ± 0.017 0.932 ± 0.014 0.943 ± 0.001 0.951 ± 0.001 Dice 0.924 ± 0.068 0.818 ± 0.097 0.793 ± 0.118 0.915 ± 0.076 0.877 ± 0.066 0.836 ± 0.077 0.922 ± 0.079 BF score 0.873 ± 0.162 0.473 ± 0.097 0.476 ± 0.107 0.834 ± 0.167 0.666 ± 0.136 0.571 ± 0.098 0.877 ± 0.153 HD95 (px) 8.362 ± 17.086 29.587 ± 26.400 30.864 ± 29.226 11.427 ± 14.699 20.499 ± 22.562 24.217 ± 23.772 8.458 ± 16.667 timg (s) 0.0072 ± 0.0004 0.0086 ± 0.0036 0.0028 ± 0.0002 0.0051 ± 0.0007 0.0069 ± 0.0001 0.0041 ± 0.0001 0.0237 ± 0.0001

In Agave salmiana, a more balanced distribution was observed. Specifically, mean IoU values are more tightly clustered (approximately 0.700–0.760) after consolidation, rel- ative to direct inference. Within this range, Mask2Former attains the highest IoU, while DeepLabV3+ remains competitive in overlap (IoU 0.756 ± 0.055), consistent with multiscale representations supporting radial structures after adaptation. However, Mask2Former again stood out in reducing error and in overall accuracy, confirming that its strength lies in more precise pixel–level classification. In addition, boundary-focused metrics further differentiate models with similar IoU: Mask2Former (and Swin–Transformer) provides the highest BF scores and the lowest HD95 values, although HD95 exhibits large disper- sion across models, indicating tile-level heterogeneity in agave plots. Models such as Swin–Transformer and SegFormer achieved acceptable performance, although without excelling in key metrics, while the CNN baselines generally show lower boundary fidelity (BF score/HD95) than the best attention-based configurations under the consolidated multi-crop setting.

The multi-species models obtained after consolidation enable analyzing performance under an operational scenario in which both morphologies coexist. As shown in Table 8, Mask2Former sustains the highest overlap (IoU) on both crops after consolidation, while Table 9 indicates that it also preserves high boundary fidelity through a strong BF score and a low HD95. This joint behavior is decisive when vegetation cover is estimated via pixel counting at orthomosaic scale. For this reason, the consolidated Mask2Former model was adopted for the final cover quantification and for computing the derived agronomic indicator, since spatially coherent contours reduce over-/under-estimation bias in soil– vegetation transition zones.

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 21 of 28


> **Table 8.**

> Evolution of the process (IoU ± standard deviation) throughout the four stages:
base training in Opuntia spp., direct inference in Agave salmiana, fine–tuning in agave and
intercropping consolidation.

Fine–Tuning

Model Base Prickly Pear

Consolidation

Inference

Consolidation

Agave

Agave

Prickly Pear

Agave

Swin–Transformer 0.885 ± 0.116 0.585 ± 0.126 0.741 ± 0.103 0.879 ± 0.116 0.738 ± 0.106 SegNet 0.597 ± 0.014 0.628 ± 0.017 0.710 ± 0.012 0.713 ± 0.046 0.700 ± 0.010 UNet–Style–Xception 0.667 ± 0.008 0.664 ± 0.007 0.685 ± 0.006 0.625 ± 0.010 0.719 ± 0.003 DeepLabV3+ 0.788 ± 0.057 0.000 ± 0.000 0.772 ± 0.049 0.758 ± 0.053 0.756 ± 0.055 U–Net 0.678 ± 0.038 0.559 ± 0.079 0.746 ± 0.064 0.660 ± 0.038 0.721 ± 0.032 SegFormer 0.799 ± 0.001 0.541 ± 0.001 0.707 ± 0.000 0.792 ± 0.000 0.715 ± 0.000 Mask2Former 0.897 ± 0.094 0.515 ± 0.015 0.754 ± 0.104 0.894 ± 0.004 0.760 ± 0.046


> **Table 9. Boundary-focused metrics after intercropping consolidation.**

Metric Swin– Transformer SegNet UNet–Style–

Xception DeepLabV3+ U–Net SegFormer Mask2Former

Dice (Opuntia) 0.950 ± 0.035 0.736 ± 0.070 0.757 ± 0.068 0.900 ± 0.051 0.796 ± 0.050 0.902 ± 0.032 0.956 ± 0.036 BF score (Opuntia) 0.952 ± 0.103 0.385 ± 0.059 0.429 ± 0.066 0.782 ± 0.153 0.425 ± 0.057 0.752 ± 0.083 0.962 ± 0.102 HD95 (px) (Opuntia) 2.759 ± 3.391 22.624 ± 11.303 20.771 ± 10.419 7.947 ± 7.758 18.276 ± 6.764 8.724 ± 5.283 2.189 ± 3.447

Dice (Agave) 0.924 ± 0.068 0.818 ± 0.097 0.793 ± 0.118 0.915 ± 0.076 0.877 ± 0.066 0.836 ± 0.077 0.922 ± 0.079 BF score (Agave) 0.873 ± 0.162 0.473 ± 0.097 0.476 ± 0.107 0.834 ± 0.167 0.666 ± 0.136 0.571 ± 0.098 0.877 ± 0.153 HD95 (px) (Agave) 8.362 ± 17.086 29.587 ± 26.400 30.864 ± 29.226 11.427 ± 14.699 20.499 ± 22.562 24.217 ± 23.772 8.458 ± 16.667

4.4. Quantification of Plant Cover

Plant cover quantification was performed using reference masks generated by man- ual annotation in LabelMe on each orthomosaic (both Opuntia spp. and Agave salmiana), establishing a binary classification {vegetation, background} (Figure 13).


> **Figure 13. Binary masks. Left: mask of Opuntia spp. Right: mask for Agave salmiana.**

These masks served as the baseline for estimating leaf area by direct pixel counting and converting pixel counts to area units based on the ground sample distance (GSD) specific to each orthomosaic. Operationally, if Nveg denotes the number of pixels labeled as vegetation and GSD the resolution in meters per pixel, the covered area was obtained as:

Aveg [m2] = Nveg × GSD2. (8)

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 22 of 28

To compare manual and automatic quantification, Mask2Former was selected as the reference architecture, given its consolidated multi-species performance and its favorable boundary fidelity. Concordance between the two approaches was assessed beyond tile- level segmentation metrics by considering an agronomic indicator derived at orthomosaic scale: leaf area. Specifically, the absolute difference ∆A = |Apred

veg −Aref

veg| and the relative percentage error

|Apred

veg −Aref

veg|

ε% = 100 ×

, (9)

Aref veg

were calculated, where Apred

veg comes from the mask segmented by Mask2Former and Aref

veg from the manual mask. The aggregated results are presented in Table 10.


> **Table 10. Crop–by–crop comparison between the coverage estimated by Mask2Former and the**

> manual reference. The vegetation pixels in both masks, the resulting areas and the absolute and
relative area errors are reported.

Apred

Aref veg (m2)

∆A (m2) ε%

Crop GSD (cm/px) Npred

veg (m2)

px Nref px

Opuntia spp. (Figure14) 1.02 527,192 516,209 55.39 54.23 1.15 2.13 Agave salmiana (Figure 15) 1.80 3,550,260 3,541,399 1150.28 1147.41 2.87 0.25


> **Figure 14. Segmentation of an RGB orthomosaic of Opuntia spp.: on the left, predicted binary**

> mask; on the right, orthomosaic with the segmentation overlay (enlarged detail). The result allows
quantifying plant cover as an agronomic indicator.

Vegetation-cover estimation at orthomosaic scale depends directly on counting pixels classified as vegetation Aveg = Nveg · GSD2 ; therefore, its validity should be interpreted jointly with overlap metrics (IoU, Dice) and contour metrics (BF score, HD95), in addition to RMSE and pixel accuracy. In particular, while IoU/Dice reflect regional agreement, BF score and HD95 explain area bias, since small boundary misalignments in soil–vegetation transitions or thin structures translate into peripheral false positives/negatives that accu- mulate in ∆A and εA. Consequently, residual discrepancies in the agronomic indicator tend to concentrate in regions of leaf occlusion/overlap and radiometrically ambiguous edges (shadows, soil texture), where the class–background separation is less stable. Under this cri- terion, architectures are prioritized that, in addition to maximizing overlap, maintain high contour fidelity, because this directly reduces the systematic error of the estimated cover.

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 23 of 28


> **Figure 15. Segmentation of an RGB orthomosaic of Agave salmiana: on the left, predicted binary**

> mask; on the right, orthomosaic with the segmentation overlay (enlarged detail). The result allows
quantifying plant cover as an agronomic indicator.


## 5. Discussion

The results show a differentiable behavior depending on crop morphology and con- firm a trade–off between precision and inference cost that, in our case, must be resolved in favor of precision. In Opuntia spp., the IoU–time relationship in Figure 16 shows that Mask2Former achieves the highest IoU, while Swin–Transformer comes close with a shorter latency. However, because the end-use objective is orthomosaic-scale cover quantification, the decision should prioritize segmentation fidelity over marginal latency reductions: a higher IoU translates into a more realistic agronomic indicator (plant cover). DeepLabV3+ and SegFormer form intermediate options: their IoU is competitive in prickly pear, and al- though SegFormer offers lower latency, that benefit does not justify sacrificing accuracy when the objective is to derive management metrics from segmentation. Classic CNNs (U–Net, U–Net Style Xception, and SegNet) achieve lower IoU scores, consistent with limitations in preserving fine edges and spatial continuity during tessellation.

Beyond the IoU–time trade-off, the inclusion of boundary-oriented criteria (BF score and HD95) provides complementary evidence on contour stability, which is critical when cover is computed by pixel counting at orthomosaic scale. Specifically, Dice/IoU quantify regional agreement, whereas BF score and HD95 capture contour alignment and near-worst- case boundary deviations, respectively; therefore, models with similar IoU can still differ in the systematic bias that propagates into leaf-area estimation. In Opuntia, this distinction is operationally relevant because pad boundaries are often fragmented by shadows and soil texture; accordingly, architectures that preserve spatially coherent contours (Table 9) are preferable when the final objective of the pipeline is an agronomic indicator rather than tile-level agreement alone.

In Agave salmiana, Figure 17 reveals complementary strengths: DeepLabV3+ and Swin–Transformer achieve IoU similar or very close to Mask2Former with shorter times. However, maintaining the previous criterion, the methodological decision must be guided by IoU, as these are radial crowns with more marked texture transitions, small precision losses have a magnified effect on leaf area estimation. In this scenario, Mask2Former remains a reference due to its spatial coherence and stability, while DeepLabV3+ excels at capturing radial patterns, and Swin–Transformer maintains high, consistent perfor- mance. SegFormer maintains the best speed/IoU ratio, which is useful when latency is a hard constraint; however, the priority for building a direct agronomic indicator should remain accuracy.

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 24 of 28

For agave, the boundary metrics help to interpret why architectures that are com- petitive in IoU may still yield different area errors: radial leaf arrangements increase the proportion of boundary pixels, making small contour shifts accumulate in peripheral false positives/negatives. Under these conditions, the HD95 and BF scores serve as informative complements to IoU/Dice, as they characterize the stability of crown edges and the extent of boundary outliers in radiometrically ambiguous zones (e.g., shadows and soil texture), which are common in semi-arid orthomosaics. Consequently, selecting a model for area estimation benefits from jointly considering overlap and boundary fidelity rather than relying on IoU alone.

The cross–domain analysis supports the need for a transfer cycle with consolida- tion. Direct inference shows selective degradations when changing morphology (prickly pear →agave), while light fine–tuning, followed by multi–species consolidation, stabilizes performance and reduces incremental relabeling. Together, the findings suggest a practical guideline: first, prioritize attention models to ensure spatial coherence and robustness in Opuntia; second, consider DeepLabV3+ and Swin–Transformer as high–precision alterna- tives in Agave, without renouncing Mask2Former when the main objective is to maximize IoU; and third, reserve latency arguments for scenarios where the processing window is strict, since, under normal conditions, the total time per orthomosaic does not displace precision as the leading criterion.


> **Figure 16.**

> IoU–Total inference time relationship in segmentation models (Orthomosaic of
Opuntia spp.).

From an operational perspective, the orthomosaic-scale pipeline and traceability, from pixel–to–pixel prediction to leaf-area estimation, enable the model output to serve as a direct agronomic indicator. Under this framework, minor improvements in IoU have a mul- tiplicative effect on estimator quality, reinforcing the convenience of selecting architectures based on their precision performance rather than marginal advantages in latency.

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 25 of 28


> **Figure 17.**

> IoU–Total inference time relationship in segmentation models (Orthomosaic of
Agave salmiana).

The observed patterns are consistent with prior evidence in agricultural segmentation: CNN baselines can be effective under controlled domains, yet robustness and contour preservation degrade under heterogeneous conditions and domain shifts [18,39]. In weed mapping and crop–weed delineation, SegNet-type approaches have shown practical value, particularly when complementary spectral cues (e.g., NDVI) strengthen vegetation dis- crimination [40]; however, recent UAV-based evaluations also report that Transformer families (e.g., SegFormer) can maintain robust performance across lighting and texture variability [41]. In this study, the advantage of attention-driven models becomes more evident when performance is evaluated using boundary-aware criteria (BF score, HD95) in addition to overlap metrics, because these metrics better reflect contour accuracy and transfer stability–two properties that directly govern orthomosaic-scale cover estimation and its derived agronomic indicators.


## 6. Limitations and Future Work

This study provides a controlled comparison of CNN- and Transformer-based seg- menters on UAV RGB orthomosaics of Opuntia spp. and Agave salmiana; however, several factors constrain the scope of the conclusions. The experiments are based on a limited number of orthomosaics and compact tile datasets, and the annotation is formulated as binary segmentation (plant vs. background) using RGB imagery only. This setup is adequate for estimating vegetation cover but does not explicitly represent other agronomically rele- vant elements, such as weeds, residues, or shadow classes. In addition, the patch-based workflow adopted for training and inference is practical and reproducible. Yet, it can attenuate long-range context and tends to concentrate residual discrepancies around soil– vegetation transitions and thin structures, which motivates complementing overlap metrics with boundary-sensitive criteria when interpreting area estimates.

As future work, we recommend extending the evaluation to additional fields and acquisition conditions (dates, phenological stages, illumination, and soil-texture variability) to strengthen the evidence of generalization. It is also relevant to move beyond binary seg- mentation toward multi-class or instance-aware formulations (crop/weed/soil/shadow) and, when available, to incorporate complementary spectral information, together with radiometric normalization, to reduce ambiguity in shadowed regions and heterogeneous backgrounds. Methodologically, overlapping tiling and explicit boundary-refinement

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 26 of 28

strategies should be assessed to stabilize orthomosaic-scale contours, along with label- efficient adaptation approaches (active learning or self-supervised pretraining) to reduce annotation cost. Finally, progressively integrating additional morphologically related crops would enable broader multi-species models and advance toward unified cover estimation in semi-arid production systems.


## 7. Conclusions

This study confirms that cross-crop transfer from Opuntia spp. to Agave salmiana is feasible when geometric standardization with pixel–to–surface traceability (via GSD), a brief domain adaptation stage, and a subsequent consolidation step are enforced at orthomosaic scale. The need for explicit adaptation is evidenced by the marked domain- shift sensitivity observed under direct inference, in which DeepLabV3+ achieved an IoU of 0.000 ± 0.000 on agave before adaptation. In contrast, fine–tuning and consolidation recovered competitive performance, reaching IoU 0.772 ± 0.049 after fine–tuning and IoU 0.756 ± 0.055 after consolidation. After intercropping consolidation, Mask2Former exhibited the most consistent multi- species behavior, attaining the highest IoU on both crops (IoU 0.894 ± 0.004 on Opuntia and IoU 0.760 ± 0.046 on Agave). Boundary-aware evaluation further supports its suitability for orthomosaic-scale cover quantification: Mask2Former achieved BF score 0.962 ± 0.102 and HD95 2.189 ± 3.447 px on Opuntia, and BF score 0.877 ± 0.153 with HD95 8.458 ± 16.667 px on Agave, indicating high contour alignment in both morphologies. Although other archi- tectures can be competitive on individual criteria, Mask2Former exhibits the most favorable joint performance across overlap and contour fidelity, which is decisive when vegetation cover is computed by pixel counting and subsequently converted to leaf area.

Overall, the proposed orthomosaic-scale protocol provides a reproducible frame- work for training, adapting, and auditing segmentation models for semi-arid succulent crops, thereby translating segmentation outputs into traceable vegetation-cover indica- tors. Beyond overlap and discrepancy metrics (IoU, RMSE, pixel accuracy), incorporating boundary-sensitive indicators (BF score, HD95) is necessary to ensure that model improve- ments correspond to reduced contour-driven bias in coverage estimation and, consequently, to more reliable agronomic indicators derived from the masks.

Author Contributions: Conceptualization, A.D.-R., C.C.-B. and E.C.-V.; methodology, A.D.-R. and C.C.-B.; software, A.D.-R. and C.C.-B.; validation, A.D.-R., C.C.-B. and E.C.-V.; formal analysis, A.D.-R. and C.C.-B.; investigation, A.D.-R., C.C.-B., E.C.-V. and M.C.-M.; resources, C.C.-B.; data curation, A.D.-R.; writing—original draft preparation, A.D.-R., C.C.-B. and E.C.-V.; writing—review and editing, A.D.-R., C.C.-B., E.C.-V. and M.C.-M.; visualization, A.D.-R., C.C.-B. and E.C.-V.; supervision, C.C.-B., E.C.-V. and M.C.-M.; project administration, M.C.-M.; All authors have read and agreed to the published version of the manuscript.

Funding: This research received no external funding.

Data Availability Statement: The complete dataset, codes, hyperparameters, backbone config- urations, and regularization criteria are publicly available on GitHub at https://github.com/ ArturoDuarteR/Semantic-Segmentation-in-Orthomosaics.git (accessed on 20 November 2025).

Conflicts of Interest: The authors declare no conflicts of interest.


## References

1. Zhang, N.; Wang, M.; Wang, N. Precision agriculture—A worldwide overview. Comput. Electron. Agric. 2002, 36, 113–132. [CrossRef] 2. Mulla, D.J. Twenty five years of remote sensing in precision agriculture: Key advances and remaining knowledge gaps. Biosyst. Eng. 2013, 114, 358–371. [CrossRef]

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 27 of 28

3. Gebbers, R.; Adamchuk, V.I. Precision agriculture and food security. Science 2010, 327, 828–831. [CrossRef] 4. Torres-Sánchez, J.; López-Granados, F.; Peña, J.M. An automatic object–based method for optimal thresholding in UAV images: Application for vegetation detection in herbaceous crops. Comput. Electron. Agric. 2015, 114, 43–52. [CrossRef] 5. Hunt, E.R., Jr.; Daughtry, C.S.T. What good are unmanned aircraft systems for agricultural remote sensing and precision agriculture? Int. J. Remote Sens. 2018, 39, 5345–5376. [CrossRef] 6. Madec, S.; Irfan, K.; Velumani, K.; Baret, F.; David, E.; Daubige, G.; Samatan, L.B.; Serouart, M.; Smith, D.; James, C.; et al. VegAnn, Vegetation Annotation of multi-crop RGB images acquired under diverse conditions for segmentation . Sci. Data 2023, 10, 302. [CrossRef] 7. Crusiol, L.G.T.; Sun, L.; Sun, Z.; Chen, R.; Wu, Y.; Ma, J.; Song, C. In–season monitoring of maize leaf water content using ground–based and UAV–based hyperspectral data. Sustainability 2022, 14, 9039. [CrossRef] 8. Jorge, A.O.S.; Costa, A.S.G.; Oliveira, M.B.P.P. Adapting to climate change with Opuntia. Plants 2023, 12, 2907. [CrossRef] 9. Servicio de Información Agroalimentaria y Pesquera (SIAP). Anuario Estadístico de la Producción Agrícola. Cierre de la Produc- ción Agrícola 2022; Cultivo «Nopal verdura» (clave 401). Available online: https://nube.agricultura.gob.mx/cierre_agricola/ (accessed on 13 May 2025). 10. Pessoa, D.V.; de Andrade, A.P.; Magalhães, A.L.R.; Teodoro, A.L.; dos Santos, D.C.; de Araújo, G.G.L.; de Medeiros, A.N.; do Nascimento, D.B.; de Lima Valença, R.; Cardoso, D.B. Forage Nutritional Differences within the Genus. J. Arid. Environ. 2020, 181, 104243. [CrossRef] 11. Michel-Cuello, C.; Aguilar-Rivera, N.; García-Pedraza, L.G.; Cárdenas-González, J.F.; Acosta-Rodríguez, I. Importance of Agave Salmiana Metab. Technol. Innov. Mezcal Agroindustry Sustainability. Progress Ind. Ecol. 2017, 11, 297–313. [CrossRef] 12. Drezner, T.D. The importance of microenvironment: Opuntia Plant Growth, Form Response Sunlight. J. Arid. Environ. 2020, 178, 104144. [CrossRef] 13. Hernández-Becerra, E.; Aguilera-Barreiro, M.d.l.A.; Contreras-Padilla, M.; Pérez-Torrero, E.; Rodriguez-Garcia, M.E. Nopal cladodes (Opuntia Ficus Indica): Nutritional properties and functional potential . J. Funct. Foods 2022, 95, 105183. [CrossRef] 14. Alducin-Martínez, C.; Ruiz Mondragón, K.Y.; Jiménez-Barrón, O.; Aguirre-Planter, E.; Gasca-Pineda, J.; Eguiarte, L.E.; Medellin, R.A. Uses, knowledge and extinction risk faced by Agave Species Mexico. Plants 2023, 12, 124. [CrossRef] 15. Ilyas, T.; Lee, J.; Won, O.; Jeong, Y.; Kim, H. Overcoming field variability: Unsupervised domain adaptation for enhanced crop–weed recognition in diverse farmlands. Front. Plant Sci. 2023, 14, 1234616. [CrossRef] [PubMed] 16. Xiang, J.; Liu, J.; Chen, D.; Xiong, Q.; Deng, C. CTFuseNet: A multi–scale CNN–Transformer feature fused network for crop type segmentation on UAV remote sensing imagery. Remote Sens. 2023, 15, 1151. [CrossRef] 17. Kamilaris, A.; Prenafeta-Boldú, F.X. Deep learning in agriculture: A survey. Comput. Electron. Agric. 2018, 147, 70–90. [CrossRef] 18. Duarte-Rangel, A.; Camacho-Bello, C.; Cornejo-Velazquez, E.; Clavel-Maqueda, M. Semantic segmentation in large–size orthomo- saics to detect the vegetation area in Opuntia spp. Crop. J. Imaging 2024, 10, 187. [CrossRef] [PubMed] 19. Gutiérrez-Lazcano, L.; Camacho-Bello, C.J.; Cornejo-Velazquez, E.; Arroyo-Núñez, J.H.; Clavel-Maqueda, M. Cuscuta Spp. Segmentation Based Unmanned Aer. Veh. (UAVs) Orthomosaics Using A U- Xception- Model. Remote Sens. 2022, 14, 4315. [CrossRef] 20. Khan, S.; Naseer, M.; Hayat, M.; Zamir, S.W.; Khan, F.S.; Shah, M. Transformers in vision: A survey. ACM Comput. Surv. 2022, 54, 1–41. [CrossRef] 21. Zhao, J.; Berge, T.W.; Geipel, J. Transformer in UAV image–based weed mapping. Remote Sens. 2023, 15, 5165. [CrossRef] 22. Guo, Z.; Cai, D.; Jin, Z.; Xu, T.; Yu, F. Research on unmanned aerial vehicle (UAV) rice field weed sensing image segmentation method based on CNN–transformer. Comput. Electron. Agric. 2025, 229, 109719. [CrossRef] 23. Xie, E.; Wang, W.; Yu, Z.; Anandkumar, A.; Alvarez, J.M.; Luo, P. SegFormer: Simple and efficient design for semantic segmentation with transformers. Adv. Neural Inf. Process. Syst. 2021, 34, 12077–12090. [CrossRef] 24. Bi, Z.; Li, Y.; Guan, J.; Li, J.; Zhang, P.; Zhang, X.; Han, Y.; Wang, L.; Guo, W. Weed identification in broomcorn millet field using SegFormer semantic segmentation based on multiple loss functions. Eng. Agric. Environ. Food 2024, 17, 27–36. [CrossRef] 25. Lin, F.; Crawford, S.; Guillot, K.; Zhang, Y.; Chen, Y.; Yuan, X.; Chen, L.; Williams, S.; Minvielle, R.; Xiao, X.; et al. MMST–ViT: Climate change–aware crop yield prediction via multi–modal spatial–temporal Vision Transformer. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), Paris, France, 1–6 October 2023 ; pp. 5774–5784. Avail- able online: https://openaccess.thecvf.com/content/ICCV2023/papers/Lin_MMST-ViT_Climate_Change-aware_Crop_Yield_ Prediction_via_Multi-Modal_Spatial-Temporal_Vision_ICCV_2023_paper.pdf (accessed on 13 May 2025). 26. Wang, B.; Chen, G.; Wen, J.; Li, L.; Jin, S.; Li, Y.; Zhou, L.; Zhang, W. SSATNet: Spectral–spatial attention transformer for hyperspectral corn image classification. Front. Plant Sci. 2025, 15, 1458978. [CrossRef] [PubMed] 27. Plascencia, L. Martha y Rogelio, custodios del maguey en Rancho La Gaspareña, Singuilucan. 7 Caníbales, 15 May 2025. Available online: https://www.7canibales.com/opinion/lalo-plascencia-opinion/ (accessed on 29 May 2025). 28. Criterio Hidalgo. Rancho La Gaspareña, de Tradición Magueyera. Criterio Hidalgo, Sección Fin de Semana, 2022. Available online: https://criteriohidalgo.com/fin-de-semana (accessed on 29 May 2025).

https://doi.org/10.3390/agriengineering8010018

AgriEngineering 2026, 8, 18 28 of 28

29. Long, J.; Shelhamer, E.; Darrell, T. Fully convolutional networks for semantic segmentation. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Boston, MA, USA, 7–12 June 2015; pp. 3431–3440. [CrossRef] 30. Ronneberger, O.; Fischer, P.; Brox, T. U–Net: Convolutional networks for biomedical image segmentation . In Proceedings of the 18th International Conference on Medical Image Computing and Computer–Assisted Intervention (MICCAI 2015), Munich, Germany, 5–9 October 2015; Springer: Berlin/Heidelberg, Germany, 2015; pp. 234–241. [CrossRef] 31. Badrinarayanan, V.; Kendall, A.; Cipolla, R. SegNet: A deep convolutional encoder–decoder architecture for image segmentation. IEEE Trans. Pattern Anal. Mach. Intell. 2017, 39, 2481–2495. [CrossRef] [PubMed] 32. Chen, L.-C.; Zhu, Y.; Papandreou, G.; Schroff, F.; Adam, H. Encoder–decoder with atrous separable convolution for semantic image segmentation. In Proceedings of the European Conference on Computer Vision (ECCV), Munich, Germany, 8–14 September 2018; Springer: Munich, Germany, 2018; pp. 801–818. [CrossRef] 33. Kolhar, S.; Jagtap, J. Leaf segmentation and counting for phenotyping of rosette plants using Xception–style U–Net and watershed algorithm. In Proceedings of the International Conference on Computer Vision and Image Processing, Rupnagar, India, 3–5 December 2021; Springer: Cham, Switzerland, 2021; pp. 139–150. [CrossRef] 34. Dosovitskiy, A.; Beyer, L.; Kolesnikov, A.; Weissenborn, D.; Zhai, X.; Unterthiner, T.; Dehghani, M.; Minderer, M.; Heigold, G.; Gelly, S.; et al. An image is worth 16×16 words: Transformers for image recognition at scale. In Proceedings of the 9th International Conference on Learning Representations (ICLR), Virtual, 3–7 May 2021; OpenReview: Virtual Event , 2021. [CrossRef] 35. Liu, Z.; Lin, Y.; Cao, Y.; Hu, H.; Wei, Y.; Zhang, Z.; Lin, S.; Guo, B. Swin Transformer: Hierarchical vision transformer using shifted windows. InProceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), Montreal, QC, Canada, 10–17 October 2021; pp. 10012–10022. [CrossRef] 36. Cheng, B.; Misra, I.; Schwing, A.G.; Kirillov, A.; Girdhar, R. Masked–attention mask transformer for universal image segmentation. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), New Orleans, LA, USA, 18–24 June 2022; pp. 1290–1299. [CrossRef] 37. Moodi, F.; Shoushtari, F.K.; Valizadeh, G.; Mazinani, D.; Salari, H.M.; Rad, H.S. Attention Xception UNet (AXUNet): A novel combination of CNN and self–attention for brain tumor segmentation. arXiv 2025, arXiv:2503.20446. [CrossRef] 38. Hossen, M.I.; Awrangjeb, M.; Pan, S.; Mamun, A.A. Transfer learning in agriculture: A review. Artif. Intell. Rev. 2025, 58, 97. [CrossRef] 39. Luo, Z.; Yang, W.; Yuan, Y.; Gou, R.; Li, X. Semantic segmentation of agricultural images: A survey. Inf. Process. Agric. 2024, 11, 172–186. [CrossRef] 40. Sa, I.; Popovi´c, M.; Khanna, R.; Chen, Z.; Lottes, P.; Liebisch, F.; Nieto, J.; Stachniss, C.; Walter, A.; Siegwart, R. WeedMap: A large–scale semantic weed mapping framework using aerial multispectral imaging and deep neural network for precision farming. Remote Sens. 2018, 10, 1423. [CrossRef] 41. Wang, Y.; Gao, X.; Sun, Y.; Liu, Y.; Wang, L.; Liu, M. SH–DeepLabv3+: An improved semantic segmentation lightweight network for corn straw cover form plot classification. Agriculture 2024, 14, 628. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.

https://doi.org/10.3390/agriengineering8010018
