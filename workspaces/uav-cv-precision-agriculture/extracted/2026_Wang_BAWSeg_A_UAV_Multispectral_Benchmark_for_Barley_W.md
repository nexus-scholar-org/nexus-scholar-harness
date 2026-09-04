---
workspace_id: SCI-000005
doi: 10.3390/rs18060915
title: 'BAWSeg: A UAV Multispectral Benchmark for Barley Weed Segmentation'
authors:
- family_name: Wang
  given_name: Haitian
  orcid: null
- family_name: Wang
  given_name: Xinyu
  orcid: null
- family_name: Ibrahim
  given_name: Muhammad
  orcid: null
- family_name: Severtson
  given_name: Dustin
  orcid: null
- family_name: Mian
  given_name: Ajmal
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:05.245695+00:00'
---

# BAWSeg: A UAV Multispectral Benchmark for Barley Weed Segmentation

Article BAWSeg: A UAV Multispectral Benchmark for Barley Weed Segmentation

Haitian Wang 1 , Xinyu Wang 1 , Muhammad Ibrahim 2 , Dustin Severtson 2 and Ajmal Mian 1,*

1 Department of Computer Science and Software Engineering, The University of Western Australia, 35 Stirling Highway, Crawley, WA 6009, Australia; haitian.wang@uwa.edu.au (H.W.); xinyu.wang@uwa.edu.au (X.W.) 2 Department of Primary Industries and Regional Development (DPIRD), Government of Western Australia, 1 Nash St., Perth, WA 6000, Australia; muhammad.ibrahim@dpird.wa.gov.au (M.I.); dustin.severtson@dpird.wa.gov.au (D.S.) * Correspondence: ajmal.mian@uwa.edu.au


## Abstract

Accurate weed mapping in cereal fields requires pixel-level segmentation from unmanned aerial vehicle (UAV) imagery that remains reliable across fields, seasons, and illumination. Existing multispectral pipelines often depend on thresholded vegetation indices, which are brittle under radiometric drift and mixed crop–weed pixels, or on single-stream convolu- tional neural network (CNN) and Transformer backbones that ingest stacked bands and indices, where radiance cues and normalized index cues interfere and reduce sensitivity to small weed clusters embedded in crop canopy. We propose VISA (Vegetation Index and Spectral Attention), a two-stream segmentation network that decouples these cues and fuses them at native resolution. The radiance stream learns from calibrated five-band reflectance using local residual convolutions, channel recalibration, spatial gating, and skip-connected decoding, which preserve fine textures, row boundaries, and small weed structures that are often weakened after ratio-based index compression. The index stream operates on vegetation-index maps with windowed self-attention to model local structure efficiently, state-space layers to propagate field-scale context without quadratic attention cost, and Slot Attention to form stable region descriptors that improve discrimination of sparse weeds under canopy mixing. To support supervised training and deployment-oriented evaluation, we introduce BAWSeg, a four-year UAV multispectral dataset collected over commercial barley paddocks in Western Australia, providing radiometrically calibrated blue, green, red, red edge, and near-infrared orthomosaics, derived vegetation indices, and dense crop, weed, and other labels with leakage-free block splits. On BAWSeg, VISA achieves 75.6% mean Intersection over Union (mIoU) and 63.5% weed Intersection over Union (IoU) with 22.8 M parameters, outperforming a multispectral SegFormer-B1 baseline by 1.2 mIoU and 1.9 weed IoU. Under cross-plot and cross-year protocols, VISA maintains 71.2% and 69.2% mIoU, respectively. The full BAWSeg benchmark dataset, VISA code, trained model weights, and protocol files will be released upon publication.

Academic Editors: Francisco Javier

Mesas Carrascosa and Fernando

Pérez Porras

Keywords: UAV; multispectral; weed mapping; barley; semantic segmentation; vegetation indices; radiometric calibration; orthomosaic; domain shift; benchmark dataset

Received: 19 February 2026

Revised: 13 March 2026

Accepted: 16 March 2026

Published: 17 March 2026

Copyright: © 2026 by the authors.


## 1. Introduction

Licensee MDPI, Basel, Switzerland.

This article is an open access article

Barley is a major cereal crop cultivated across temperate and semi-arid regions world- wide, forming a core component of cereal-based farming systems alongside wheat and canola [1,2]. Across these systems, weeds remain the primary biotic constraint on yield,

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license.

Remote Sens. 2026, 18, 915 https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 2 of 23

causing around 13% average global yield loss and billions of dollars of annual economic impact due to competition and herbicide resistance [3–6]. Herbicide-resistant populations of grass and broadleaf weeds are now common in many intensive cereal regions, motivating strong demand for spatially explicit weed management strategies.

In barley-based cropping systems, species such as annual ryegrass (Lolium rigidum) and wild radish (Raphanus raphanistrum) often dominate the weed spectrum, driving double-digit yield and quality losses when control is delayed or ineffective [7–10]. These pressures highlight the need for high-resolution sensing and mapping approaches capable of delineating weed patches at sub-field scales to support site-specific management [11,12].

Current practice in precision weed management combines manual scouting with proximal and remote sensing technologies, including satellite imagery, crewed aircraft sur- veys, and UAV-based multispectral imaging. These pipelines typically compute vegetation indices and apply threshold rules or shallow classifiers to distinguish crop, weed, and soil classes [11,13,14]. However, their reliance on hand-crafted indices, per-tile parameter tuning, and independent pixel or patch decisions limits robustness under variable illu- mination, canopy closure, and mixed crop–weed cover [15–17]. Deep convolutional and Transformer-based encoder–decoder architectures improve spatial coherence but often rely on a single concatenated feature stream and are rarely evaluated under strong spatial or temporal domain shifts in cereal systems [18–21]. Despite rapid progress, publicly available benchmarks for weed segmentation do not yet match the practical deployment setting of cereal paddocks [22]. Many widely used weed datasets focus on image-level recognition or close-range field imagery, rather than field-scale UAV orthomosaics with pixel-level crop–weed masks. Large-scale aerial agriculture datasets (e.g., Agriculture-Vision) pro- vide RGB–NIR patches with anomaly-style masks such as weed clusters, but they are not designed as calibrated multi-band UAV orthomosaics for explicit crop–weed semantic seg- mentation across multiple seasons and fields. As a consequence, prior work often reports results on single-field or single-season splits, making it difficult to quantify generalization under realistic spatial and temporal shifts.

To address these limitations, we propose VISA (Vegetation Index and Spectral At- tention), a two-stream segmentation network that separates radiance-based and index- based reasoning. The radiance branch preserves fine row and patch boundaries through residual attention modules, while the index branch captures plot-level contextual pat- terns using attention and state-space mechanisms. Native-resolution features from both streams are fused to produce accurate crop–weed–background predictions, demonstrat- ing improved segmentation performance under mixed canopy, variable illumination, and domain-shift conditions.

To enable supervised learning and deployment-oriented evaluation in cereal sys- tems, we introduce BAWSeg, a four-year UAV multispectral benchmark collected over two commercial barley paddocks near Kondinin, Western Australia (2020–2023), using a DJI Phantom 4 Multispectral platform with real-time kinematic (RTK) positioning and an upward irradiance sensor. Each campaign provides radiometrically calibrated five-band reflectance orthomosaics (blue, green, red, red edge, and near infrared), five derived vege- tation indices, namely normalized difference vegetation index (NDVI), green normalized difference vegetation index (GNDVI), enhanced vegetation index (EVI), soil-adjusted vege- tation index (SAVI), and modified soil-adjusted vegetation index (MSAVI) , and dense pixel annotations for crop, weed, and other classes that explicitly address crop–weed canopy mixing. Unlike existing resources that are either close-range field imagery or aerial datasets with anomaly-style labels, BAWSeg is designed as a reproducible UAV orthomosaic bench- mark with consistent radiometry and leakage-free spatial block splits. These splits support three evaluation protocols—within-plot, cross-plot, and cross-year (Figure 1)—so that gen-

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 3 of 23

eralization across paddocks and seasons can be measured under realistic domain shifts rather than optimistic random sampling.


> **Figure 1. Overview of UAV multispectral data collection and BAWSeg dataset construction. The**

> pipeline includes flight acquisition with RTK and irradiance sensors, radiometric calibration, or-
thorectification, stitching, feature extraction, annotation, and resulting crop–weed–soil maps.

We evaluate VISA on BAWSeg under three deployment-oriented protocols, namely within-plot, cross-plot, and cross-year, so that performance can be examined under both in-domain testing and spatiotemporal transfer. The experimental study includes protocol- level evaluation, comparisons with representative baselines, and ablation analysis to assess whether decoupled radiance and vegetation-index modelling improves robustness across paddocks and seasons. Quantitative findings are presented in the Results Section and summarized in the Conclusions Section.

Our main contributions are summarized as follows:

• VISA model: a two-stream network that integrates radiance and vegetation-index reasoning for improved segmentation under mixed canopy scenarios. • BAWSeg benchmark: a UAV multispectral dataset for barley fields with high- resolution, pixel-level crop, weed, and soil annotations under realistic field and seasonal variations. • Evaluation protocol: systematic within-plot, cross-plot, and cross-year benchmarks that demonstrate the utility of BAWSeg for model assessment and precision weed mapping research.


## 2. Related Work

We group prior work into three areas: UAV multispectral weed mapping with index- based pipelines, crop–weed semantic segmentation using convolutional encoder–decoder networks on RGB or multispectral inputs, and Transformer or state-space models for remote sensing segmentation. These studies provide the baselines and context for our two-stream radiance–index model.

UAV multispectral imagery is widely used for site-specific weed management and crop–weed discrimination, typically by deriving vegetation indices such as NDVI, GNDVI, SAVI and MSAVI from calibrated red, green, red edge and near-infrared bands and then classifying crop, weed and soil with threshold rules or shallow models including support vector machines, random forests and multilayer perceptrons [13,14,23–25]. Object-based image analysis combined with random forests has been used to segment homogeneous regions and generate prescription maps in maize and sunflower, while exploiting only local spectral and texture descriptors [26–28]. Semi-supervised systems and feature se- lection schemes further improve robustness under limited labels by stacking multiple vegetation indices into per-pixel or small-patch feature vectors for weed mapping in het- erogeneous fields [15,29,30]. More recent work integrates multispectral UAV data with ancillary information and ensemble learners to estimate weed density at the plot scale in cereal crops [16,31,32]. Across these studies, decisions are usually taken independently for each pixel or patch using hand-designed spectral indices and hard labels that assign a

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 4 of 23

single class per pixel, which restricts the use of row-level and field-level structure and does not explicitly model the uncertainty of mixed pixels where crop plants and weeds occupy the same footprint.

UAV crop–weed mapping has increasingly been formulated as semantic segmentation with convolutional or encoder–decoder backbones such as U-Net, SegNet and DeepLabv3+, adapted from generic vision to field imagery [18–20]. Early agricultural deployments trained fully convolutional networks on UAV or ground imagery to delineate crop rows and weed patches but largely followed single-stream designs [21,25,33]. Most studies use RGB or multispectral bands and append a small set of vegetation indices as extra channels, and then feed the concatenated tensor into one encoder that must learn spectral contrast and geometric texture without explicit separation of radiance and normalized index cues [21,25,34]. Architectures that dedicate an index-aware branch or explicitly decouple spectral ratio information from spatial structure remain uncommon in the UAV literature, as summarized by recent reviews of deep learning for weed detection and drone imaging in agriculture [17,35]. Supervision typically relies on hard one-hot pixel labels, so mixed pixels where crops and weeds co-occur are forced to a single class and label uncertainty is rarely modeled [17,33]. These choices limit robustness under illumination change and can reduce sensitivity to small weed clusters embedded in crop canopies in orthomosaics [25,34,36].

Transformer architectures have been adopted for remote sensing segmentation to capture long-range dependencies that are difficult for convolutional encoders. Early work adapts the Vision Transformer and Swin Transformer to aerial and satellite imagery using self-attention on patch tokens or shifted windows [37,38], followed by hybrids such as Seg- Former and related CNN Transformer models with lightweight decoders for high-resolution land cover from RGB or multispectral inputs [39,40]. Subsequent methods specialize Trans- formers for remote sensing through tailored tokenization and encoder–decoder designs, including RSTFormer and UNetFormer for urban scenes and river networks and Spec- tralFormer for hyperspectral land cover classification [41–43]. In agriculture, Transformer variants are mainly used for crop type mapping and field-level weed detection from UAV or satellite imagery with single-stream ViT-style backbones on reflectance stacks or RGB composites and hard pixel labels [44,45]. Recent Mamba-based segmentation studies have expanded this direction in remote sensing. RS3Mamba introduced a dual-branch visual state-space design for remote sensing image semantic segmentation, while MFMamba extended Mamba to multimodal remote sensing segmentation through image and DSM fusion [46,47]. Further 2024–2025 studies explored efficient or multiscale Mamba-based decoders for high-resolution scene parsing, including a semantic-Transformer-assisted real-time model, a Vision Mamba model with multiscale multi-frequency fusion, and LMVMamba with adaptation fine-tuning [48–50]. Importantly, for agricultural scenes, EGCM-UNet addressed farmland remote sensing image semantic segmentation, and U-MoEMamba reported Mamba-based UAV segmentation results for cabbage heads under complex field conditions [51,52]. Nevertheless, most Transformer- and Mamba-based ap- proaches still employ a single feature stream without explicit vegetation-index reasoning, structured grouping modules such as Slot Attention, or annotation protocols that represent mixed crop–weed canopies and soft label uncertainty.


## 3. Materials and Methods

This section specifies the complete workflow used to build the BAWSeg benchmark and develop the VISA segmentation model. It first describes the UAV acquisition setup, radiometric calibration and preprocessing steps that produce georeferenced multispectral orthomosaics, followed by the annotation procedure, patch extraction, and leakage-free

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 5 of 23

block splits that support within-plot, cross-plot, and cross-year evaluation. It then details the two-stream architecture, feature fusion, training objective, and implementation settings used consistently across all experiments.

3.1. Dataset Construction

We first give details of the BAWSeg dataset, since the segmentation model is designed to exploit the information available in this dataset. BAWSeg is a multispectral dataset collected by a UAV from repeated field campaigns. It covers platform and radiometric calibration, mission geometry for uniform coverage, and preprocessing that rectifies, coreg- isters, orthorectifies, and mosaics all bands. It then outlines patch extraction, leakage-free splits, augmentation, and a dense polygon-based pixel annotation protocol with quality control. The process preserves traceability and consistent radiometry and geometry for reliable training and evaluation.

3.1.1. Acquisition Platform and Configuration

Image capture used a DJI Phantom 4 Multispectral (P4M) remotely piloted aircraft system (RPAS) (SZ DJI Technology Co., Ltd., Shenzhen, China) with six synchronized cameras, five narrowband monochrome sensors (blue, green, red, red edge and near- infrared (NIR)) and one RGB sensor. The platform includes an integrated spectral sunlight sensor. In our workflow, the irradiance associated with each single-band image was obtained from the XMP metadata field Irradiance stored in the TIFF output of the aircraft. These per-image irradiance records were retained together with the image metadata, while an RTK module with TimeSync referenced geotags to the camera center. The gimbal was fixed at nadir (−90◦). Exposure control operated in manual mode with fixed white balance and ISO for each mission, and shutter speed was set to avoid motion blur at the commanded groundspeed. Radiometric reference data were collected with a calibrated Lambertian reflectance panel using nadir frames acquired before and after each mission and whenever the solar zenith changed noticeably during flight, with the irradiance sensor enabled for all captures. Simple capture quality gates monitored shutter speed, saturation, irradiance validity and gimbal status, and any pass that violated these checks was repeated at the same altitude and speed. During acquisition, EXIF metadata recorded exposure parameters, RTK position, ellipsoidal height, gimbal yaw, pitch and roll, and irradiance flags. After each mission, these fields were parsed into a CSV file with frame identifiers, timestamps, platform pose and quality indicators. All data were stored in a mission-specific directory hierarchy indexed by date and site with separate locations for raw multispectral and RGB frames, metadata tables and integrity checksums, which preserves capture conditions for the radiometric normalization and orthomosaic generation described in the next subsection.

3.1.2. Flight Mission Geometry and Coverage

Two experimental barley fields near Kondinin, Western Australia, were surveyed in four UAV campaigns from 2020 to 2023. The mapped polygons, centred at E2 (lat −32.508363, lon 118.338139) and E8 (lat −32.516563, lon 118.353799), cover 0.6046 \  \text {km}^ 2

in total. Missions were planned in DJI Ground Station Pro (DJI GS Pro, version 2.0.17, SZ DJI Technology Co., Ltd., Shenzhen, China) using lawnmower patterns within each polygon, with the camera fixed at nadir, flight altitude set to 120 \ \text {m} above ground level, and both forward and side overlap set to 80\ %. For the DJI Phantom 4 Multispectral, this flight altitude corresponds to a nominal multispectral ground sample distance of approxi- mately 6.35 \ \text {cm/pixel}, following the manufacturer specification (H/18.9) \ \text {cm/pixel}, where

H denotes the flight altitude relative to the mapped surface. At this resolution, crop-row structure and multi-row weed patches remain spatially resolved in the orthomosaic, which is consistent with the patch-level semantic segmentation setting used in BAWSeg. However,

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 6 of 23

very small isolated weeds and heavily occluded seedlings may occupy only a few pixels, which limits separability at the finest spatial scale. Line spacing, trigger intervals and groundspeed were derived from these parameters and applied uniformly during acquisi- tion. Takeoff and landing points were placed on access tracks outside the cropped area and flights were scheduled between 10:30 and 14:30 local time, with segments repeated if wind or illumination changed noticeably to keep conditions consistent within each field. For every sortie, the mission plan and realised trajectory were logged with the field identifier, including polygon vertices, line spacing and commanded speed. Figure 2 illustrates the resulting coverage pattern, where survey lines follow the field boundaries and provide stable overlap for subsequent orthomosaic generation and feature matching across the four campaigns.


> **Figure 2. Planned Planned flight paths for the Kondinin experimental fields. Left, E8 polygon and**

> survey lines planned in GSPro. Right, E2 polygon with the same overlap and altitude parameters.
The parallel survey lines indicate the planned lawnmower flight trajectories within each field polygon.
The inset shows a representative interior tile used for quality control of row orientation and texture.

3.1.3. Image Preprocessing

Raw multispectral frames were converted to single-precision arrays, filtered by capture quality flags, and denoised with a 3 × 3 median kernel applied independently to the R, G, B, NIR and RedEdge bands. We selected this as a mild nonlinear denoising step to suppress isolated impulsive artifacts while preserving stronger local edges before cross- band registration and reflectance processing. However, because the operation is local, very small weed responses near the spatial resolution limit may be weakened when they occupy only one to two pixels. Frames that contained more than 0.5% saturated pixels in any band were discarded, and lens vignetting and distortion were corrected using the vendor calibration so that all subsequent steps operated on rectified images. Cross-band alignment then registered every band to the green reference. SIFT keypoints were extracted per band, descriptor matches were filtered with a Lowe ratio test and RANSAC, and a projective homography was estimated for each band, which is adequate for the near-planar scenes at 120 m altitude. The transform was refined by maximizing the enhanced correlation coefficient on a grid of small windows and registration quality is reported as the median reprojection error, with frames above a 0.5 pixel threshold flagged for reprocessing. Figure 3 illustrates typical inlier correspondences after matching and RANSAC.

Panel-based radiometric calibration converted the registered digital numbers to per- band reflectance that is consistent across sorties. For each frame, the irradiance term was obtained from the per-image XMP metadata field Irradiance recorded by the aircraft. For each band, a scale factor was then derived jointly from the pre-flight and post-flight panel

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 7 of 23

captures and these per-image irradiance values, and the frame reflectance was adjusted for exposure and illumination variation, clipped to a fixed range, and stored as float32. Orthorectification then used RTK geotags and structure from motion in Agisoft Metashape Professional (version 2.0.1, Agisoft LLC, St. Petersburg, Russia) to estimate camera poses and a digital elevation model. All bands of each frame were treated as a rigid group and were projected onto the elevation model into a common ground coordinate system. Seamline optimization and blending within the overlap generated multispectral and RGB orthomosaics without exposure compensation for the analytical bands so that radiometric consistency was preserved. The final per-band mosaics were exported as tiled GeoTIFFs for index computation and patch extraction in the dataset pipeline.


> **Figure 3. Example of keypoint inliers for cross-band and inter-frame alignment. Green circles denote**

> SIFT keypoints and blue lines denote matches retained after RANSAC.

3.1.4. Annotation and Dataset Finalization

Pixels in the multispectral orthomosaics were labelled at native resolution as barley crop, ryegrass weed, or other, where other covers soil, wheel tracks, and infrastructure. Orthorectified and radiometrically normalized mosaics were tiled, and a vegetation mask derived from NDVI restricted annotation to canopy pixels while nonvegetation and invalid pixels were assigned other or an ignore value. Within this mask, annotators used QGIS (version 3.22 LTR, QGIS Development Team, Open Source Geospatial Foundation (OSGeo), Beaverton, OR, USA) with orthomosaic, NDVI and RGB composites to draw crop and weed polygons, and very small polygons were discarded. The polygons were rasterised by assigning each pixel the class of the polygon that contained its centre, overlaps were resolved in favour of weed polygons so that mixed canopies followed the weed label, and remaining vegetation pixels outside all polygons were kept as other. Each tile was annotated by one operator and checked by a second, and a stratified subset was reannotated to maintain consistent class usage across fields and years. The final labels were stored as single-channel GeoTIFFs with other equal to zero, crop equal to one, weed equal to two and ignore equal to two hundred and fifty five, and during training, this map was converted to one-hot targets y_{b,c,h , w}\ in \{0,1\ }, with the ignore value forming a binary mask that removed those pixels from the supervised loss. Representative examples of the RGB orthomosaic, reflectance map, and final hard label map are shown in Figure 4.

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 8 of 23


> **Figure 4. From left to right, RGB orthomosaic, a single-band reflectance map, and the hard label map.**

> Green denotes crop, red denotes weed, and white denotes other.

3.2. Methods

We propose VISA, a two-stream segmentation architecture that leverages complemen- tary cues from vegetation indices and multispectral imagery. The model aims to jointly capture fine spatial detail and field-scale agronomic patterns that are difficult to resolve from a single feature stream. As shown in Figure 5, the network contains two parallel branches, a Vegetation Index Branch that operates on normalized vegetation indices and a Spectral Residual Attention Branch (SRAB) that processes the multispectral radiance cube. Both branches output 64-channel feature maps at native 256 \times  256 resolution, which are fused by a shallow head to produce per-pixel logits for crop, weed, and background classes. This design separates low-level radiometric reasoning from high-level vegetation context modelling, improving robustness under illumination changes and canopy mixing. Let B denote batch size. Each training sample is a 256 × 256 patch cropped from a georeferenced orthomosaic. The radiance input is a five-band reflectance tensor Xraw ∈RB×5×H×W with

H = W = 256, ordered as (B, G, R, RE, NIR) after band co-registration. The index input is a five-channel tensor Xidx ∈RB×5×H×W formed by vegetation-index maps computed from the same reflectance bands. Unless otherwise stated, convolutions use zero padding and preserve spatial size. Both branches output native-resolution features in RB×64×256×256 and are fused to predict C = 3 semantic classes {other, crop, weed}, while the ignore label is excluded from supervision by a binary mask. The configuration used throughout the paper fixes the embedding width at d = 64, the window size at s = 8 for windowed self-attention, the number of Slot Attention groups at K = 6, and the number of Slot Attention refinement iterations at T = 3.

3.2.1. Vegetation-Index Modelling Branch

To complement raw-band learning with normalized spectral reasoning, we introduce a vegetation-index modelling branch that operates on a compact stack of five indices {NDVI, GNDVI, EVI, SAVI, MSAVI} derived from calibrated reflectance. These five indices were selected to provide complementary responses within the five-band sensing capa- bility of the DJI Phantom 4 Multispectral. NDVI serves as a standard vegetation-vigor baseline. GNDVI increases sensitivity to chlorophyll variation through the green band. EVI incorporates the blue band and is less sensitive to canopy background and satura- tion at higher vegetation density. SAVI and MSAVI explicitly reduce soil-background effects, which is relevant in BAWSeg because the four-year barley scenes include both partially exposed soil and incomplete canopy closure. Therefore, we selected indices that jointly capture canopy vigor, chlorophyll-sensitive variation, reduced saturation, and soil-adjusted vegetation response, rather than relying on a single family of closely related ratios. Indices are computed from calibrated reflectance with a small stabilizer ϵ = 10−6.

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 9 of 23

For example, NDVI = (NIR −R)/(NIR + R + ϵ), GNDVI = (NIR −G)/(NIR + G + ϵ), and SAVI = 1.5(NIR −R)/(NIR + R + 0.5 + ϵ). We apply a fixed per-index standard- ization using statistics computed on the training split only. For the ith index channel,

˜Xidx

i = (Xidx

i −µi)/(σi + ϵ), and the same (µi, σi) are reused for validation and test data to avoid leakage.


> **Figure 5. Overview of the proposed pipeline. Bottom: SRAB radiance stream with residual attention**

> and a U-Net decoder. Top: vegetation-index stream with windowed self-attention, Mamba blocks, Slot
Attention with mean-slot broadcast, and a scale-aligned refinement module. Here, the scale-aligned
refinement module denotes the lightweight feature-refinement stage that aligns the index-stream
representation with the radiance branch on the native 256 \times 
256 grid before fusion. Right: fusion head
that concatenates the two 64-channel feature maps at the native resolution to generate class logits.

Each index map is linearly standardized and projected to an embedding width d = 64 via a 1 × 1 convolution and LayerNorm:

Z = \tex t {LN } (W^{\ma t h rm {proj}} \tilde X^{\mathrm {idx}} + b^{\mathrm {proj}}), \quad Z \in \mathbb {R}^{B\times d\times 256\times 256}.  (1)

Here, Wproj ∈Rd×5×1×1 and bproj ∈Rd implement a 1 × 1 projection from five indices to d = 64 channels. LN(·) denotes LayerNorm applied over the channel dimension at each spatial location, which stabilizes training under index magnitude variations across seasons and fields.

We reshape Z into non-overlapping 8 × 8 windows and apply two lightweight Trans- former encoder layers with windowed self-attention. This design preserves local spatial coherence (e.g., crop rows and patch textures) while avoiding the quadratic complexity of global attention. A decomposed relative positional bias further enhances geometric sensitivity within each window.

Concretely, Z is partitioned into Nw = (H/s)(W/s) non-overlapping windows. For each window, we flatten its s × s grid into a token matrix U ∈Rn×d with n = s2. Multi-head attention uses h heads with per-head width dh = d/h. For head j, queries, keys, and values are Qj = UWQ

j , where WQ

j ∈Rd×dh. The attention output is computed as

j , Kj = UWK

j , and Vj = UWV

j , WK

j , WV

_ j(U)

S

= \ma

t hrm

\mathr m {Attn}

oftmax}\!\left (\frac {Q_j K_j^{\top }}{\sqrt {d_h}} + B^{\mathrm {rel}}_j\right )V_j,  (2)

{

j ∈Rn×n is a learnable relative positional bias indexed by 2D offsets within the

where Brel

window. The h head outputs are concatenated and projected back to width d by WO ∈Rd×d.

Each encoder layer follows a pre-norm residual form

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 10 of 23

\ h a t U = U + \ ma t hr m {WSA}( \mathrm {LN}(U)),\qquad U^{+} = \hat U + \mathrm {FFN}(\mathrm {LN}(\hat U)),  (3)

where WSA denotes the multi-head windowed attention above. FFN is a position-wise two-layer perceptron with GELU nonlinearity applied independently to each token. In our configuration, s = 8 and h = 8, which keeps attention local to 64 tokens per window while preserving row-level texture cues.

To capture field-wide regularities, we append two Mamba-style state-space blocks that act as gated 1D filters along the token sequence. For token embedding ut, the selective update follows:

x_ { t+ 1 } = \ b ar A \odot x_t + \bar B \odot (u_t \odot \sigma (W_g u_t))  (4)

We apply the state-space blocks on a 1D token sequence obtained by a row-major raster scan of the H × W grid, giving L = HW tokens. The current implementation uses a single scan order only and does not adopt bidirectional, reverse, or cross-scanning variants. At step t, ut ∈Rd is the token embedding and xt ∈Rd is the state vector. ¯A ∈Rd and ¯B ∈Rd

are learned per-channel coefficients after discretization, and ⊙denotes element-wise mul- tiplication. The gate σ(Wgut) uses Wg ∈Rd×d and modulates input injection to suppress ambiguous mixed pixels. In this design, directional bias is partially mitigated because the sequential module operates after windowed self-attention with relative positional bias, while spatial augmentation by rotations and flips is applied during training. This recur- rence updates each token in linear time in L and does not incur the quadratic cost of global attention, which is important for field-scale context modelling on dense orthomosaics.

Finally, we apply Slot Attention (K = 6 slots, T = 3 iterations) to group tokens into structured semantic regions (e.g., crop canopy, weed clusters, soil). The aggregated descrip- tor is broadcasted back to the spatial grid, forming a feature map Fidx ∈RB×64×256×256

that carries globally consistent vegetation cues. Let U+ ∈RL×d denote the token matrix after windowed attention and state-space filtering. Slot Attention maintains K slot vectors S = {sk}K

k=1 with sk ∈Rd. At each refinement iteration, we compute attention weights between tokens and slots by

}

!

=\frac {\exp

\

t,k

a_ {

;W^{k}u_t\rangle /\sqrt {d}\right )} {\sum _{k'=1}^{K}\exp \!\left (\langle W^{q}s_{k'},\;W^{k}u_t\rangle /\sqrt {d}\right )},  (5)

,

a

\l

ngle W^ {q}s_k

\

eft (\l

where ut is the tth token, Wq, Wk ∈Rd×d, and ⟨·, ·⟩is the dot product. Slot updates aggregate values vt = Wvut with Wv ∈Rd×d,

e l ta

s_k = \ su m _{t=1} ^{L} a_{t,k}\,v_t, \qquad s_k \leftarrow \mathrm {GRU}(s_k,\Delta s_k) + \mathrm {MLP}(\mathrm {LN}(s_k)),  (6)

\ D

where the GRU and MLP are shared across slots. After T iterations, we compute the mean- slot descriptor m = 1

t = U+

K ∑K

k=1 sk and broadcast it to all spatial locations by Ub

t + Wbm with Wb ∈Rd×d. This mean-slot broadcast injects a global grouping prior while retaining token-level variation for small weed clusters. Finally, Ub is reshaped back to RB×d×H×W

and mapped to Fidx by a 3 × 3 convolution followed by normalization.

The resulting feature map is then passed to a scale-aligned refinement module, which consists of lightweight convolutional refinement layers applied on the native 256 \times  256 grid. Its role is to refine the index-stream representation before fusion and to align it with the radiance branch while preserving the contextual information aggregated by the Transformer, Mamba, and Slot Attention modules. The refined index feature map is addi- tionally supervised by an auxiliary segmentation loss weighted by 0.3, which encourages discriminative learning in the index domain.

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 11 of 23

3.2.2. Spectral Residual Attention Branch

In parallel, the spectral residual attention branch learns directly from calibrated multi- spectral reflectance {B, G, R, RE, NIR} rather than from normalized vegetation-index ratios. This choice preserves local band-specific contrast at native resolution, including weak spectral discontinuities along crop–weed boundaries, fine row texture, and fragmented responses from small weed patches that may be attenuated after ratio-based compression. The branch adopts a three-stage residual-attention encoder followed by a symmetric de- coder. Local residual convolutions capture short-range spatial detail, while the attention components reweight informative channels and spatial locations under task supervision.

Each stage stacks two residual-attention units consisting of convolutional bodies, squeeze–excitation channel weighting, and CBAM-style spatial gating. Formally, a unit transforms feature U as

Y = \math r m { CBAM}\! \ left (\mathrm {SE}\!\left (U + W_2 * \operatorname {GELU}(W_1 * U)\right )\right )  (7)

In this unit, W1 and W2 are 3 × 3 convolutions that preserve spatial size. The residual branch U + W2 ∗GELU(W1 ∗U) increases nonlinearity while keeping gradient flow stable.

The squeeze–excitation operator produces channel weights from global statistics. Let g = 1 HW ∑h,w U:,h,w ∈RC be global average-pooled features for C channels. SE computes a = σ


## 1 and Wse

2
are learned linear layers and σ(·) is the sigmoid.

Wse


## 2 GELU(Wse

1 g)


and rescales channels by Use

c,h,w = ac Uc,h,w, where Wse

 

CBAM further applies spatial gating conditioned on local context. Given Use, we form a spatial descriptor by concatenating average-pooled and max-pooled maps across channels and apply a 7 × 7 convolution to obtain a spatial mask Msp ∈[0, 1]H×W. The output is Yc,h,w = Msp

h,w Use

c,h,w, which suppresses background clutter and enhances thin weed structures aligned with crop rows.

Encoded features with widths {64, 128, 256} are hierarchically aggregated by trans- posed convolutions and refinement blocks, restoring the native 256 × 256 resolution. The resulting feature map Fraw ∈RB×64×256×256 encodes high-frequency appearance cues com- plementary to the vegetation-index pathway. Skip connections from the encoder to the decoder help preserve boundary localization and reduce the loss of thin or spatially sparse weed structures during downsampling.

The encoder uses three resolution levels with channel widths {64, 128, 256}. Spatial resolution is reduced by a factor of two between levels, and the decoder restores the 256 × 256 resolution with learnable upsampling. Skip connections from the three encoder levels are concatenated into the corresponding decoder stages to preserve row boundaries and small weed fragments that are lost under repeated downsampling. The last decoder stage outputs Fraw at width 64 to match the index branch for fusion.

Together, these two streams—one semantic and index-driven, the other spectral and residual-attentive—form a dual-branch encoder that captures both normalized vegetation signals and raw spectral variations for robust UAV weed segmentation.

3.2.3. Feature Fusion and Prediction Head

After decoding, the two streams provide aligned native-resolution feature maps with complementary content: the radiance stream preserves high-frequency textures and spectral contrast, whereas the index stream injects global semantic priors shaped by attention and state-space filtering. The fusion head performs local channel mixing and produces per-pixel logits for the target classes.

Both feature maps are aligned on the same 256 × 256 grid and share the same channel width, which allows fusion without interpolation. The classifier predicts C = 3 logits per

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 12 of 23

pixel and the ignore label is implemented only in the supervision mask rather than as a prediction class.

Let Yraw, Yidx ∈RB×64×256×256 be the branch outputs at native resolution. They are concatenated along the channel axis to form Fcat = Concat(Yraw, Yidx) ∈RB×128×256×256. The fusion block first performs channel mixing and local aggregation by a 3 × 3 convolution with zero padding, followed by batch normalization and a rectified linear activation. Denote the fusion kernel Wfus ∈R64×128×3×3 and bias bfus ∈R64. The pre-activation fused map F ∈RB×64×256×256 is defined component-wise as

F_{b,q , h,w} \ ;=\; (\Wfus \ conv

F ^ { \ m athrm {cat}})_{b,q,h,w} \;+\; \Bfus _{q}, \qquad 1 \le q \le 64 . \label {eq:fuse-compact}  (8)

Batch normalization with learned affine parameters γq, βq and an ε-stabilized variance is then applied per output channel, followed by a rectified activation. Writing µq and σ2

q for the batch-wise moments of Fb,q,:,:,

}

a

\!\left \{ 0 ,\; \ g

F'_{b,q , h,w

a mm

=\m ax

_q\frac {F_{b,q,h,w}-\mu _q}{\sqrt {\sigma _q^2+\varepsilon }}+\beta _q\right \}.  (9)

The prediction head maps F′ to C semantic classes by a 1×1 convolution Wcls ∈RC×64×1×1

with bias bcls ∈RC to produce the per-pixel logits Z ∈RB×C×256×256:

h, w }=\

_{q=1}^ {6

sum

4}W^{\m a thrm  { c l s } }_{c,q,1,1}\;F'_{b,q,h,w}+b^{\mathrm {cls}}_{c}, \quad 1\le c\le C.  (10)

Z_{b,c ,

Class posteriors are obtained by a temperature-scaled softmax over the class dimension with τ = 1 during training and inference,

i

,

gned} P_{b

\begin  {al

\! \ b ig (Z_{b,c,h,w}/\tau \big )} {\sum _{c'=1}^{C}\exp \!\big (Z_{b,c',h,w}/\tau \big )}, P &\in \mathbb {R}^{B\times C\times 256\times 256}. \end {aligned} \label {eq:softmax}  (11)

c,

\

frac {\exp

h,w} &=

Training minimizes a class-balanced cross-entropy on the fused logits with an ignore mask for unlabeled pixels. Let Ωbe the set of labeled pixels over a mini-batch and yb,c,h,w ∈{0, 1} be the one-hot targets. Class weights wc follow median-frequency balancing with pixel frequencies fc measured on the training set, that is, wc = median( f1, . . . , fC)/ fc. The primary loss is

t h rm

\ m a t

hca l  {L}_{\ma

{c e}} =-\f rac {1}{|\Omega |}\sum _{(b,h,w)\in \Omega }\ \sum _{c=1}^{C} w_c\,y_{b,c,h,w}\,\log P_{b,c,h,w}.  (12)

To improve robustness to class imbalance and to sharpen thin weed boundaries, we add a soft Dice term and an edge-aware term computed on the labeled pixels. Let Pb,c,h,w be the fused posterior in (11) and yb,c,h,w be the one-hot target. The Dice loss is

a l {L}_{\ma th

rm {dice}} =1-\frac {

\ma t h c

1}^ {C} P_{b , c ,h,w}\,y_{b,c,h,w}+\epsilon } {\sum _{(b,h,w)\in \Omega }\sum _{c=1}^{C} P_{b,c,h,w}+\sum _{(b,h,w)\in \Omega }\sum _{c=1}^{C} y_{b,c,h,w}+\epsilon }.  (13)

2\sum _{(b ,h ,w) \in \Ome g a }\sum _{ c=

For edge supervision, we compute boundary maps by a fixed Sobel operator ∇ap- plied channel-wise to the class posteriors and labels. Define E(P) = ∑C

c=1∥∇Pc∥1 and E(y) = ∑C

c=1∥∇yc∥1 on Ω. The edge loss uses an ℓ1 penalty

\ma t h cal   {L}_{\mat

hrm {edge}} =\frac {1

}{|\Omega |}\sum _{(b,h,w)\in \Omega }\left |E(P)_{b,h,w}-E(y)_{b,h,w}\right |.  (14)

The fused objective is the weighted combination

\ma t hca l {L}_{\mat h rm {fuse}}=\mathcal {L}_{\mathrm {ce}}+\lambda _{\mathrm {dice}}\mathcal {L}_{\mathrm {dice}}+\lambda _{\mathrm {edge}}\mathcal {L}_{\mathrm {edge}},  (15)

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 13 of 23

where λdice and λedge are fixed across all experiments.

The total objective is L = Lfuse + α Lidx

aux with α = 0.3, where Lidx

aux is the auxiliary cross-entropy applied to Yidx after a 1×1 prediction layer. Gradients flow through the fusion block into both branches. At inference, the per-pixel label is ˆcb,h,w = arg maxc Pb,c,h,w and the corresponding confidence is maxc Pb,c,h,w, which is exported with the segmentation map for downstream decision modules.


## 4. Results

We report results for the proposed radiance-index two-stream model on BAWSeg under three deployment-oriented protocols, namely within-plot, cross-plot, and cross-year. Performance is computed on held-out spatial blocks using mean Intersection over Union (mIoU), per-class IoU, micro-averaged precision, recall and F1, overall accuracy (OA), and Cohen’s κ [53]. For mIoU confidence intervals (CIs), we use a block bootstrap that resamples test blocks with replacement and recomputes the metric per replicate [54]. Unless stated otherwise, all metrics exclude ignore pixels.

4.1. Experimental Setting

Hardware and software. All experiments ran on a single workstation with Ubuntu 22.04.4 LTS, an AMD Ryzen 9 7950X CPU, 32 GB RAM, a 2 TB NVMe SSD, and one NVIDIA GeForce RTX 4090 GPU with 24 GB VRAM. The software stack used Python 3.10 and PyTorch 2.7 with CUDA 12.6. Training used automatic mixed precision, and evaluation used FP32. For reproducibility, we fixed a single global seed of 2026 across Python, NumPy, and PyTorch. We disabled cuDNN benchmarking and enabled deterministic algorithms where available, following PyTorch reproducibility guidance [55].

Training configuration. Models were trained for 50 epochs on 256 × 256 patches. Optimization used AdamW [56] with β1 = 0.9, β2 = 0.999, weight decay 0.01, and gradient clipping with a global norm of 1.0. The initial learning rate was set to 6 × 10−4 and decayed with a cosine schedule after a linear warm-up of 1500 iterations. The effective batch size was 16. Inputs were standardized per band or per index using training-set statistics. Data augmentation used spatial transforms only, including random horizontal and vertical flips and random rotations in {0◦, 90◦, 180◦, 270◦}, which preserves calibrated reflectance semantics.

Losses and inference. Training minimized a class-balanced cross-entropy on fused logits with an ignore mask, plus an auxiliary cross-entropy applied to the index stream with weight α = 0.3. Inference used single-scale evaluation at native patch resolution. For block-level evaluation, we applied a sliding window over each held-out block using 256 × 256 windows with stride 128 and averaged logits in overlapping regions before taking the argmax label map. This prevents boundary artifacts from dominating block metrics.

Metrics and confidence intervals. For class c, IoU is IoUc = TPc TPc+FPc+FNc computed over labeled pixels. Mean IoU averages over the three classes. Micro-precision, micro-recall, and micro-F1 are computed from the summed confusion counts across all classes and all blocks. Cohen’s κ is computed from the confusion matrix using standard chance correction for nominal labels [53]. For each reported CI, we draw 10,000 bootstrap replicates at the block level and take the 2.5 and 97.5 percentiles of the resulting mIoU distribution [54]. Block-level resampling is used because adjacent pixels inside an orthomosaic are spatially correlated, and evaluation based on spatially independent partitions is the standard practice in remote sensing segmentation benchmarks [57].

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 14 of 23

4.2. Segmentation Across Plots and Years


> **Figure 6 summarizes training dynamics across 50 epochs. The fused loss decreases**

> steadily and validation mIoU increases until convergence, with the best checkpoint selected
by validation mIoU. The final checkpoint is used for all protocol evaluations.


> **Figure 6. Training dynamics of the proposed model. The upper panel shows loss, accuracy, mean**

> IoU, precision, recall and F1 over 50 epochs. The lower panel shows precision versus recall for each
epoch. Markers move towards the upper right region as training progresses and stabilise near the
final operating point.


> **Table 1 reports within-plot performance stratified by year and field. Mean IoU re-**

> mains in the range [0.748, 0.763] across the eight year–field combinations, with weed IoU
consistently above 0.62. Micro-F1 remains close to 0.84, while OA remains close to 0.95 and
κ remains close to 0.79. These results indicate stable behavior across acquisition years for
the same operational region and sensor configuration.


> **Table 1. Within-plot segmentation performance per year and field on held-out test blocks. Mean IoU**

> is estimated using 95% bootstrap confidence intervals. Precision, recall and F1 are micro-averaged
over all classes.

Per Class IoU Micro Metrics Global Metrics

Year Field mIoU

Crop Weed Other P R F1 OA κ

2020 E2 0.748 0.842 0.621 0.781 0.838 0.846 0.842 0.943 0.784 E8 0.751 0.844 0.623 0.786 0.840 0.848 0.844 0.944 0.786

2021 E2 0.754 0.845 0.626 0.791 0.842 0.850 0.846 0.945 0.789 E8 0.759 0.848 0.630 0.800 0.844 0.852 0.848 0.946 0.791

2022 E2 0.762 0.850 0.636 0.801 0.846 0.854 0.850 0.947 0.795 E8 0.760 0.849 0.633 0.798 0.845 0.853 0.849 0.947 0.793

2023 E2 0.757 0.846 0.632 0.794 0.843 0.851 0.847 0.946 0.792 E8 0.763 0.851 0.638 0.800 0.848 0.856 0.852 0.948 0.799


> **Table 2 summarizes protocol-level generalization. Under within-plot evaluation, the**

> model reaches mIoU 0.756 ± 0.004 with weed IoU 0.635. Under cross-plot transfer, training
on one field and testing on the other yields mIoU near 0.71, and the primary degradation
appears in the weed class, while crop IoU remains close to the within-plot level. Under
cross-year testing, training on 2020–2022 and testing on 2023 yields mIoU 0.692 ± 0.007
and weed IoU 0.544, with crop IoU remaining above 0.83. The larger drop in the cross-year
setting is mainly attributable to temporal domain shift across acquisition years, which
changes weed morphology, weed density, canopy mixing, exposed-soil proportion, and
residual illumination conditions in the orthomosaics. This effect is concentrated in the
weed class, while crop IoU remains comparatively stable, indicating that the degradation
is driven primarily by year-dependent variation in weed appearance rather than by a

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 15 of 23

general failure of preprocessing or radiometric calibration. Across protocols, the relative sensitivity is concentrated in weed IoU, while OA stays above 0.93, reflecting the strong class imbalance between vegetation and the less frequent weed pixels.


> **Table 2. Segmentation performance under different evaluation protocols. Train and test sets are**

> defined at the block level. Mean IoU is reported with 95% confidence intervals.

Per Class IoU Micro Metrics Global Metrics

Protocol Train Set Test Set mIoU ± CI

Crop Weed Other P R F1 OA κ

Within plot E2 and E8, 2020 to 2023 E2 and E8, 2020 to 2023 0.756 ± 0.004 0.847 0.635 0.794 0.851 0.843 0.847 0.946 0.794 Cross plot E2, 2020 to 2023 E8, 2020 to 2023 0.712 ± 0.006 0.840 0.576 0.724 0.838 0.830 0.834 0.937 0.768 Cross plot E8, 2020 to 2023 E2, 2020 to 2023 0.718 ± 0.006 0.846 0.584 0.724 0.842 0.836 0.839 0.939 0.773 Cross year 2020 to 2022, E2 and E8 2023, E2 and E8 0.692 ± 0.007 0.832 0.544 0.700 0.828 0.816 0.822 0.936 0.752

4.3. Comparison with Existing Methods


> **Table 3 compares the proposed model with an index-based classical baseline and repre-**

> sentative CNN and Transformer segmentation networks under the within-plot protocol. All
deep baselines were trained and evaluated using the same block splits, patch size, optimizer
type, learning-rate schedule family, and number of epochs as the proposed model. For
multispectral inputs, we adapted the first layer of each architecture to accept five channels.
For models that use patch embeddings, we replaced the input projection to accept five
channels and initialized added channel weights by copying the mean of RGB weights when
ImageNet pretraining was used, and then fine-tuned end-to-end on BAWSeg.


> **Table 3. Comparison with classical baselines and modern segmentation networks under the within**

> plot protocol on E2 and E8 from 2020 to 2023. MSI denotes the five calibrated multispectral bands
and indices denote the five vegetation indices. Mean IoU is reported with 95% bootstrap confidence
intervals over test blocks.

Method Year/Venue Input mIoU ± CI Crop IoU Weed IoU Others IoU F1 OA κ Params (M)

RF + Indices [58] 2021 ML Indices 0.674 ± 0.010 0.812 0.532 0.679 0.734 0.907 0.703 0.2 SegNet RGB [19] 2019 TPAMI RGB 0.694 ± 0.009 0.825 0.558 0.699 0.752 0.915 0.718 29.4 SegNet MSI [19] 2024 TPAMI MSI 0.702 ± 0.009 0.831 0.567 0.708 0.759 0.918 0.724 29.5 U-Net RGB [18] 2023 MICCAI RGB 0.712 ± 0.008 0.836 0.579 0.720 0.768 0.922 0.732 31.0 U-Net MSI [18] 2022 MICCAI MSI 0.731 ± 0.007 0.842 0.594 0.758 0.783 0.930 0.748 31.1 UNet++ MSI [59] 2024 DLMIA MSI 0.735 ± 0.007 0.844 0.603 0.759 0.787 0.932 0.751 34.2 DeepLabv3 R50 RGB [60] 2020 arXiv RGB 0.724 ± 0.008 0.838 0.585 0.748 0.775 0.928 0.743 41.1 DeepLabv3+ R50 MSI [20] 2024 ECCV MSI 0.738 ± 0.007 0.845 0.609 0.761 0.788 0.933 0.753 43.3 PSPNet R50 RGB [61] 2023 CVPR RGB 0.720 ± 0.008 0.835 0.582 0.743 0.772 0.927 0.739 46.3 HRNetV2 W18 MSI [62] 2022 TPAMI MSI 0.740 ± 0.007 0.846 0.611 0.763 0.792 0.934 0.756 65.8 BiSeNetV2 RGB [63] 2021 IJCV RGB 0.707 ± 0.009 0.829 0.566 0.726 0.764 0.921 0.729 13.4 SegFormer B0 RGB [39] 2021 NeurIPS RGB 0.732 ± 0.007 0.843 0.598 0.755 0.784 0.931 0.749 13.7 SegFormer B1 RGB [39] 2021 NeurIPS RGB 0.736 ± 0.007 0.846 0.602 0.760 0.787 0.933 0.752 27.6 SegFormer B1 MSI [39] 2023 NeurIPS MSI 0.744 ± 0.005 0.847 0.616 0.769 0.793 0.943 0.786 27.8 Ours 2026 MSI 0.756 ± 0.004 0.847 0.635 0.794 0.847 0.946 0.794 22.8

The random forest baseline uses the five vegetation indices as input features and predicts per-pixel labels, followed by a 3 × 3 majority filter to remove isolated predictions. It achieves mIoU 0.674 ± 0.010 with weed IoU 0.532, which quantifies the gap between index-threshold style pipelines and learned dense segmentation on calibrated mosaics.

Among deep baselines, the strongest multispectral model in this comparison is SegFormer-B1 with MSI input, which achieves mIoU 0.744 ± 0.005 and weed IoU 0.616. Convolutional multispectral models such as U-Net MSI and DeepLabv3+ MSI achieve mIoU in the 0.73 to 0.74 range with weed IoU below 0.61. The proposed two-stream fusion achieves mIoU 0.756 ± 0.004 and weed IoU 0.635 with 22.8M parameters. Relative to SegFormer-B1 MSI, this corresponds to a +0.012 absolute improvement in mIoU and a +0.019 improvement in weed IoU under matched splits and evaluation. These gains are

consistent with separating calibrated radiance cues from index cues and fusing them at

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 16 of 23

native resolution, rather than forcing a single encoder to learn both signal types from a concatenated input.

4.4. Ablation Study


> **Table 4 reports ablations under the within-plot protocol. Each variant modifies one**

> factor while keeping the same training configuration, random seed, optimizer, schedule,
and data splits. Reported mIoU values include block-bootstrap CIs computed with the
same procedure as the main results. Throughput is measured at batch size 1 using FP16
inference on an RTX 4090, with 20 warm-up iterations and 200 timed iterations, and GPU
timing synchronized before and after each iteration.


> **Table 4. Ablation on the within-plot protocol. ∆is relative to the full model. Params in millions.**

> FLOPs in billions at 256 × 256. Mem in GB at FP16, batch size 1. mIoU reports block-bootstrap 95%
confidence intervals. Arrows indicate whether higher or lower values are preferable.

Variant mIoU ↑ ∆ Weed IoU ↑ Params (M) ↓ FLOPs (G) ↓ Mem (GB) ↓ FPS ↑

Module removal or replacement

Full model 0.756 ± 0.004 0.000 0.635 22.8 33.6 2.60 78 w/o VIMB (RAW only) 0.731 ± 0.007 −0.025 0.596 9.6 25.4 2.20 92 w/o relative bias in WSA 0.749 ± 0.007 −0.007 0.626 12.8 33.4 2.60 78 w/o Slot Attention 0.744 ± 0.007 −0.012 0.618 12.3 32.4 2.50 80 w/o mean-slot broadcast 0.748 ± 0.007 −0.008 0.622 12.3 32.4 2.50 80 Single-scale decoder (idx stream) 0.747 ± 0.007 −0.009 0.621 12.6 32.7 2.55 80

Quantity changes

WSA heads h = 4 0.750 ± 0.007 −0.006 0.627 12.8 33.5 2.60 78 WSA heads h = 8 (full) 0.756 ± 0.004 0.000 0.635 12.8 33.6 2.60 78 WSA heads h = 12 0.758 ± 0.007 +0.002 0.637 12.9 34.4 2.70 74 Mamba layers L = 0 0.738 ± 0.007 −0.018 0.610 12.2 31.5 2.50 82 Mamba layers L = 1 0.746 ± 0.007 −0.010 0.624 12.5 32.5 2.55 79 Mamba layers L = 2 (full) 0.756 ± 0.004 0.000 0.635 12.8 33.6 2.60 78 Mamba layers L = 3 0.757 ± 0.007 +0.001 0.637 13.1 34.9 2.70 75 Notes. FLOPs: measured with fvcore (count MACs as FLOPs), input 1 × C × 256 × 256, eval() and Dropout off. Mem: PyTorch max-allocated GPU memory (FP16, batch = 1). FPS: average over 200 iterations after 20 warm-ups, timing wrapped by torch.cuda.synchronize(). Unless noted, differences ≤0.007 mIoU are not statistically significant under block-level bootstrap.

Removing the vegetation-index modelling branch yields the largest accuracy drop, reducing mIoU from 0.756 to 0.731 and weed IoU from 0.635 to 0.596, while reducing param- eters and increasing FPS. This isolates the contribution of index-based context beyond what is learned from calibrated multispectral bands alone. Within the index stream, removing relative positional bias in windowed self-attention reduces mIoU to 0.749, and removing Slot Attention reduces mIoU to 0.744 with a concurrent weed IoU decrease, indicating that grouping tokens into region descriptors contributes to weed discrimination under canopy mixing. Removing the mean-slot broadcast reduces mIoU to 0.748, which shows that re-injecting a global descriptor into the spatial grid affects final predictions beyond the slot aggregation itself.

Varying attention heads shows a compute–accuracy trade-off. Reducing heads to h = 4 decreases mIoU to 0.750 with a minor weed IoU decrease. Increasing heads to h = 12 yields mIoU 0.758 while reducing FPS due to higher attention cost. For the state-space component, removing Mamba layers produces a clear reduction to 0.738 mIoU and 0.610 weed IoU, and performance improves monotonically up to two layers, with limited change from two to three layers at increased compute and memory. Across these variants, improvements below the ablation CI scale in Table 4 should be interpreted as small under the block-bootstrap uncertainty, while changes above that scale correspond to consistent differences under the same evaluation procedure.

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 17 of 23


## 5. Discussion

The evaluation protocols expose two distinct regimes. When training and testing on disjoint spatial blocks from the same paddocks and seasons, VISA reaches 0.756 mIoU and 0.635 weed IoU, indicating that the model can separate weed patches from barley canopy at orthomosaic resolution while preserving row structure. Under cross-plot testing, mIoU drops to about 0.71 and the degradation concentrates on the weed class, while crop IoU remains close to the within-plot level. The same pattern holds under cross-year testing, where mIoU decreases to 0.692 and weed IoU to 0.544, with crop IoU still above 0.83. This behaviour is consistent with operational conditions in cereal systems, where crop appearance is relatively regular within a growth stage, while weed pressure, phenology, and within-row occlusion vary strongly across paddocks and seasons. Therefore, the results suggest that the remaining generalization gap is driven less by background and crop variation and more by shifts in weed morphology, density, and canopy mixing.

A key design choice in VISA is to prevent the radiance cues and index cues from com- peting inside a single encoder. Vegetation indices suppress many illumination and exposure effects by construction and encode cross-band interactions that correlate with chlorophyll and canopy vigor, which makes them informative for vegetation delineation across flights. At the same time, indices compress radiometric detail and can attenuate subtle within- canopy contrasts that differentiate sparse weeds from barley leaves, especially when the canopy is dense and when soil is largely occluded. Conversely, calibrated multispectral reflectance retains high-frequency textures, row boundaries, and small spectral deviations that are informative for fine weed clusters, but this signal is more sensitive to residual radiometric drift and to local mosaic artefacts. VISA keeps these cues in separate pathways so that the radiance stream can preserve boundary detail without being dominated by normalized ratios, and the index stream can capture stable vegetation patterns without being distracted by band-specific noise. The fusion at native resolution then combines boundary precision from the radiance stream with context from the index stream, which aligns with the observed gains over a single-stream SegFormer baseline at a similar scale.

The ablation study helps interpret which components contribute to weed robustness. Removing the index branch reduces mIoU by 0.025 and lowers weed IoU from 0.635 to 0.596, indicating that vegetation-index reasoning contributes materially beyond what can be learned from calibrated bands alone. Within the index branch, windowed self-attention supports local structure and row-consistent patterns, and the relative positional bias yields a consistent mIoU reduction when removed, which is expected because row geometry is expressed primarily through relative offsets rather than absolute location in a tile. The state- space layers provide the largest single improvement among the index-branch modules, with a 0.018 mIoU drop when they are removed, which suggests that linear-time context propagation helps encode plot-scale regularities that extend beyond the attention window. Slot Attention further improves weed sensitivity, with a 0.012 mIoU drop when removed, consistent with the role of region-level grouping in stabilizing representations of sparse and fragmented weed patches embedded in crop canopies. The mean-slot broadcast contributes an additional margin, indicating that injecting a global descriptor back to the spatial grid helps resolve local ambiguity in mixed pixels.

The sequential component in the index branch also merits clarification with respect to scan direction. In the current model, the Mamba-style state-space blocks use a single row-major raster scan to convert the 2D feature grid into a 1D sequence. We do not use bidirectional or cross-scanning in this study. A multi-directional design could, in principle, reduce directional bias further for anisotropic field structure. However, in the present architecture, the sequential module is preceded by windowed self-attention with relative positional bias, and the training pipeline includes rotation and flip augmentation, which

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 18 of 23

already reduce sensitivity to a fixed scan order. In addition, the inputs are orthorectified and radiometrically calibrated before sequence construction, so residual viewing and illumination effects are primarily handled in preprocessing rather than by changing scan direction. Under this setting, we did not observe evidence in the protocol-level results that scan order was a dominant source of error. Therefore, we retained the single-scan formulation to preserve the lightweight design of the index branch, while regarding multi- directional scanning as a possible extension for future work.

The selected index set should also be distinguished from the vegetation-index products provided in standard DJI software workflows. For Phantom 4 Multispectral data, DJI Terra provides NDVI, GNDVI, NDRE, LCI, and OSAVI, which only partially overlap with the index set used in this study. Our choice of NDVI, GNDVI, EVI, SAVI, and MSAVI was guided by the need to retain one blue-band index and two soil-adjusted indices that are directly relevant to mixed-canopy and exposed-soil conditions in BAWSeg. In future deployment-oriented settings, vendor-generated indices could be used as an alternative index source if one aims to simplify the preprocessing workflow. However, they would define a different input space from the one used here and, therefore, should be treated as a new variant that requires retraining and revalidation rather than as a direct replacement.

The platform also provides a co-registered RGB stream, which could be combined with multispectral data in future extensions. In such a setting, RGB would mainly contribute visible texture, edge, and morphological detail, while the multispectral bands provide red edge and near-infrared responses that are more informative for vegetation condition and crop–weed discrimination under mixed canopy and illumination variation. Their combination is, therefore, most relevant for boundary refinement, delineation of small weed patches, and visually ambiguous regions where appearance and spectral cues are both needed. We did not include RGB fusion in the present study because our objective was to establish a controlled benchmark for multispectral reflectance and vegetation-index modelling only. Adding RGB would define a different multimodal setting and should be evaluated as a separate extension under the same block-based protocols.

BAWSeg is constructed to make these conclusions meaningful under realistic de- ployment constraints. The dataset spans four seasons across two commercial paddocks, includes calibrated five-band orthomosaics and a consistent set of vegetation indices, and uses leakage-free spatial blocks for training and testing. Block splits are critical in ortho- mosaic learning because random sampling can place near-duplicate textures and lighting conditions in both training and test sets, yielding optimistic estimates that do not trans- late across paddocks. The cross-plot and cross-year protocols further stress the model under changes in weed distribution and season-specific appearance, which are the primary sources of failure in practice. The relatively stable crop IoU across protocols indicates that the calibration and preprocessing pipeline produces consistent crop appearance, while the weed IoU drop under shift highlights the need for modelling choices and training strategies that target rare, small, and occluded weed structures. This limitation is related to both acquisition scale and preprocessing. At the nominal multispectral GSD of about 6.35 \ \text {cm/pixel} at 120 m altitude, BAWSeg is well suited to row-level and patch-level weed segmentation, but very small weeds near the spatial resolution limit are inherently more difficult to separate from crop canopy and mixed pixels. The 3 \times  3 median filter used in preprocessing improves robustness to isolated pixel noise and helps stabilize subsequent alignment and reflectance processing, but it can also attenuate one to two pixel weed responses before feature extraction. Therefore, we regard the current preprocessing as a practical trade-off that improves overall orthomosaic quality while leaving very small weed detectability as a residual limitation of the pipeline.

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 19 of 23

From a precision agriculture perspective, the reported performance should be inter- preted together with the efficiency results in Table 4. The full model uses 22.8 M parameters, 33.6 GFLOPs, 2.60 GB FP16 memory, and runs at 78 FPS for 256 \times  256 patches on a single RTX 4090. These results indicate that the model is practical for routine post-flight deploy- ment on a standard workstation, where tiled orthomosaics can be segmented efficiently for same-cycle weed mapping, targeted scouting, and prescription preparation. In this workflow, the dominant time cost is more likely to come from orthomosaic generation and preprocessing rather than from network inference itself. The confidence maps produced by the softmax output further support risk-aware filtering, where low-confidence weed detections can be flagged for manual inspection instead of immediate treatment. This makes the current system more suitable for reliable offline decision support than for direct onboard UAV inference, which is consistent with common agronomic practice.

Several limitations remain. First, the geographic scope is limited to two paddocks in one grainbelt region and one UAV sensor configuration, so the reported cross-year robustness does not fully characterize transfer to different soil types, management practices, or imaging systems. Second, the labels represent three classes and resolve crop and weed overlap by polygon precedence, which is operationally convenient but does not capture the fractional composition of mixed pixels in dense canopy. This affects both training targets and evaluation, especially when weeds are small and partially occluded. Third, orthomosaic generation can introduce seamline artefacts and local blur that change with overlap and wind conditions, which can act as nuisance variation across campaigns. Addressing these constraints motivates several concrete directions. Expanding BAWSeg to additional farms and sensors would improve coverage of radiometric and agronomic variability. Introducing probabilistic or soft labels near ambiguous boundaries and in mixed-canopy regions would better match the underlying physical mixture. For generalization, domain generalization and test-time adaptation strategies that operate on calibrated reflectance and indices are promising, since the cross-plot and cross-year drops are concentrated in the weed class. Finally, weakly supervised extensions that exploit unlabeled mosaics from new seasons could reduce annotation burden while improving robustness to the shifts that are most salient in deployment.


## 6. Conclusions

In this paper, we presented BAWSeg, a four-year UAV multispectral benchmark for barley weed segmentation collected over two commercial paddocks in Western Australia. BAWSeg provides radiometrically calibrated five-band reflectance orthomosaics (blue, green, red, red edge, and near-infrared), derived vegetation-index maps, and dense pixel annotations for crop, weed, and other classes, together with leakage-free spatial block splits and deployment-oriented evaluation protocols. Building on this benchmark, we proposed VISA, a two-stream segmentation architecture that decouples radiance-based learning from vegetation-index reasoning and fuses both cues at native resolution to improve robustness under mixed-canopy conditions. Across the BAWSeg evaluation suite, VISA achieves a within-plot mIoU of 0.756 with a weed IoU of 0.635 and overall accuracy of 0.946 using 22.8 M parameters, and it retains an mIoU of 0.712 under cross-plot transfer and 0.692 under cross-year testing.

Beyond accuracy gains, our results show that explicitly modelling vegetation-index structure complements calibrated radiance features and improves weed sensitivity under challenging field variability. The ablation study supports this conclusion: removing the index branch yields a 0.025 mIoU decrease, indicating that index-driven context contributes materially to final predictions. BAWSeg and VISA together offer a reproducible foundation for benchmarking multispectral crop–weed segmentation under realistic spatial and tem-

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 20 of 23

poral shifts, and for developing models that better generalize across seasons and paddocks. To facilitate follow-up research and practical adoption, we will release the BAWSeg dataset, the VISA implementation, and trained model weights upon publication.

Author Contributions: Conceptualization, H.W. and A.M.; Methodology, H.W., M.I. and A.M.; Software, H.W.; Validation, H.W., M.I., D.S. and X.W.; Formal analysis, H.W.; Investigation, H.W., M.I. and D.S.; Resources, M.I., D.S. and A.M.; Data curation, H.W., M.I., D.S. and X.W.; Writing—original draft preparation, H.W.; Writing—review and editing, H.W., M.I., D.S., X.W. and A.M.; Visualization, H.W. and X.W.; Supervision, A.M.; Project administration, A.M. and M.I.; Funding acquisition, A.M. and M.I. All authors have read and agreed to the published version of the manuscript.

Funding: This research received no external funding.

Data Availability Statement: A public preview subset of the underlying multispectral weed-detection dataset is available on IEEE DataPort: Haitian Wang, Xinyu Wang, Muhammad Ibrahim, Dustin Severtson, Ajmal Mian, “Multispectral Remote Sensing for Weed Detection in West Australian Agricultural Lands”, IEEE DataPort, 11 February 2026, doi: https://doi.org/10.21227/f8e1-5934. The full BAWSeg benchmark dataset, together with the VISA implementation source code, trained model weights, and protocol files, will be released upon publication of this article.

Acknowledgments: The authors acknowledge the support from The University of Western Australia and the Department of Primary Industries and Regional Development (DPIRD), Government of Western Australia. We thank the field site owners and operational staff in the Kondinin region for enabling repeated UAV data collection across multiple seasons, and we acknowledge the assistance and advice from collaborators involved in field logistics, data curation, and annotation quality control. The authors reviewed and edited the content and take full responsibility for the final manuscript.

Conflicts of Interest: The authors declare no conflicts of interest.

Abbreviations

The following abbreviations are used in this manuscript:

BAWSeg Barley Weed Segmentation benchmark dataset VISA Vegetation-Index and Spectral Attention (two-stream segmentation network) UAV Unmanned Aerial Vehicle RPAS Remotely Piloted Aircraft System RTK Real-Time Kinematic RGB Red, Green, and Blue NIR Near-Infrared RE Red Edge NDVI Normalized Difference Vegetation Index GNDVI Green Normalized Difference Vegetation Index EVI Enhanced Vegetation Index SAVI Soil-Adjusted Vegetation Index MSAVI Modified Soil-Adjusted Vegetation Index SIFT Scale-Invariant Feature Transform RANSAC Random Sample Consensus WSA Windowed Self-Attention SE Squeeze-and-Excitation CBAM Convolutional Block Attention Module GRU Gated Recurrent Unit mIoU mean Intersection over Union IoU Intersection over Union OA Overall Accuracy

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 21 of 23

CI Confidence Interval FP16 16-bit Floating Point FP32 32-bit Floating Point


## References

1. ABARES. Australian Crop Report; Technical Report Issue; Australian Bureau of Agricultural and Resource Economics and Sciences (ABARES): Canberra, Australia, 2023. 2. Grain Industry Association of Western Australia. Barley Council Crop Report and Industry Outlook; Technical Report; Grain Industry Association of Western Australia: Perth, Australia, 2023. 3. Pacanoski, Z.; Mehmeti, A. Weeds and Their Impact on Crop Production. Plants 2021, 10, 1–18. 4. Oerke, E.C.; Dehne, H.W.; Schönbeck, F. Yield Losses in Major Crops Due to Weeds and Other Pests. Crop Prot. 2021, 143, 105552. 5. Llewellyn, R.; Ronning, D.; Ouzman, J.; Walker, S.; Mayfield, A.; Clarke, M. Impact of Weeds on Australian Grain Production; Technical Report; Grains Research and Development Corporation (GRDC): Canberra, Australia, 2016. 6. Powles, S.B.; Yu, Q. Evolution in Action: Plants Resistant to Herbicides. Annu. Rev. Plant Biol. 2010, 61, 317–347. [CrossRef] [PubMed] 7. Walsh, M.J.; Harrington, R.B.; Powles, S.B. Harrington Seed Destructor: A New Non Chemical Weed Control Tool for Global Grain Crops. Crop Sci. 2012, 52, 1343–1347. [CrossRef] 8. Broster, J.C.; Koetz, E.; Wu, H. A Survey of Weed Flora and Weed Management Practices in the Australian Grain Industry. Weed Biol. Manag. 2019, 19, 111–120. 9. Reeves, T.G.; Code, G.; Sutherland, A. The Effect of Annual Ryegrass (Lolium rigidum) on Yield of Cereals in Mediterranean Type Environments. Aust. J. Exp. Agric. 2018, 58, 412–420. 10. Eslami, S.V.; Gill, G.S.; Bellotti, B.; McDonald, G. Wild Radish (Raphanus raphanistrum) Interference in Wheat. Weed Sci. 2006, 54, 749–756. 11. Chlingaryan, A.; Sukkarieh, S.; Whelan, B. Machine Learning Approaches for Crop Yield Prediction and Nitrogen Status Estimation in Precision Agriculture: A Review. Comput. Electron. Agric. 2018, 151, 61–69. [CrossRef] 12. Lambert, J.; Tisseyre, B.; Guillaume, S. Weed Mapping in Arable Fields Using Low Altitude Imagery Acquired by Unmanned Aerial Vehicles. Precis. Agric. 2018, 19, 684–698. 13. López-Granados, F. Weed Detection for Site Specific Weed Management: Mapping and Real Time Approaches. Weed Res. 2011, 51, 1–11. [CrossRef] 14. López-Granados, F.; Torres-Sánchez, J.; De Castro, A.I.; Serrano-Pérez, A.; Mesas-Carrascosa, F.J.; Peña, J.M. Early Season Weed Mapping in Sunflower Using UAV Technology: Variability of Herbicide Treatment Maps Against Weed Thresholds. Precis. Agric. 2016, 17, 183–199. [CrossRef] 15. Pérez-Ortiz, M.; Peña, J.M.; Gutiérrez, P.A.; Torres-Sánchez, J.; Hervas-Martínez, C.; López-Granados, F. Selecting Patterns and Features for Between and Within Crop Row Weed Mapping Using UAV Imagery. Expert Syst. Appl. 2016, 47, 85–94. [CrossRef] 16. Jin, X.; Xu, X.; Yang, G.; Feng, H.; Li, Z.; Shen, J. Consistent Improvements in Weed Mapping Performance in Corn Fields Leveraging Multisource Remote Sensing Data and Machine Learning Methods. Front. Plant Sci. 2023, 14, 1237256. 17. Murad, N.Y.; Mahmood, T.; Forkan, A.R.M.; Morshed, A.; Jayaraman, P.P.; Siddiqui, M.S. Weed detection using deep learning: A systematic literature review. Sensors 2023, 23, 3670. 18. Ronneberger, O.; Fischer, P.; Brox, T. U Net: Convolutional Networks for Biomedical Image Segmentation. In Proceedings of the Med- ical Image Computing and Computer Assisted Intervention; Springer International Publishing: Cham, Switzerland, 2015; pp. 234–241. 19. Badrinarayanan, V.; Kendall, A.; Cipolla, R. SegNet: A Deep Convolutional Encoder Decoder Architecture for Image Segmentation. IEEE Trans. Pattern Anal. Mach. Intell. 2017, 39, 2481–2495. [CrossRef] 20. Chen, L.C.; Zhu, Y.; Papandreou, G.; Schroff, F.; Adam, H. Encoder Decoder with Atrous Separable Convolution for Semantic Image Segmentation. In Proceedings of the European Conference on Computer Vision; Springer: Berlin/Heidelberg, Germany, 2018; pp. 801–818. 21. Lottes, P.; Behley, J.; Milioto, A.; Stachniss, C. UAV-based Crop and Weed Classification Using Fully Convolutional Networks. In Proceedings of the ICRA, Singapore, 29 May–3 June 2017; IEEE: Piscataway, NJ, USA, 2017; pp. 5157–5163. 22. Wang, H.; Ibrahim, M.; Miao, Y.; Severtson, D.; Mansoor, A.; Mian, A.S. Multispectral Remote Sensing for Weed Detection in West Australian Agricultural Lands. In Proceedings of the 2024 International Conference on Digital Image Computing: Techniques and Applications (DICTA); IEEE: Piscataway, NJ, USA, 2024; pp. 624–631. 23. Peña, J.M.; Torres-Sánchez, J.; de Castro, A.I.; Kelly, M.; López-Granados, F. Weed Mapping in Early Season Maize Fields Using Object Based Analysis of Unmanned Aerial Vehicle Images. PLoS ONE 2013, 8, e77151. [CrossRef] 24. Wang, H.; Wang, Y.; Wang, X.; Miao, Y.; Zhang, Y.; Zhang, Y.; Mansoor, A. P2MFDS: A Privacy-Preserving Multimodal Fall Detection System for Elderly People in Bathroom Environments. In Proceedings of the International Conference on Artificial Intelligence of Things and Systems; Springer: Berlin/Heidelberg, Germany, 2025; pp. 129–146.

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 22 of 23

25. De Castro, A.I.; Torres-Sánchez, J.; Peña, J.M.; Jiménez-Brenes, F.M.; Csillik, O.; López-Granados, F. An Automatic Random Forest OBIA Algorithm for Early Weed Mapping Between and Within Crop Rows Using UAV Imagery. Remote Sens. 2018, 10, 285. [CrossRef] 26. Castaldi, F.; Pelosi, F.; Pascucci, S.; Casa, R. Assessing the Potential of Images from Unmanned Aerial Vehicles to Support Herbicide Patch Spraying in Maize. Precis. Agric. 2017, 18, 76–94. [CrossRef] 27. Pérez-Ortiz, M.; Peña, J.M.; Gutiérrez, P.A.; Torres-Sánchez, J.; Hervas-Martínez, C.; López-Granados, F. A Semi Supervised System for Weed Mapping in Sunflower Crops Using Unmanned Aerial Vehicle Imagery. Appl. Soft Comput. 2015, 37, 533–544. [CrossRef] 28. Ciceklidag, P.; Ibrahim, M.; Wang, H.; Miao, Y.; Hong, J.; Hassan, G.M.; Mian, A.S. High-Definition 3D Point Cloud Mapping of the City of Subiaco in Western Australia. In Proceedings of the DICTA; IEEE: Piscataway, NJ, USA, 2024. 29. Tamouridou, A.A.; Alexandridis, T.K.; Pantazi, X.E.; Lagopodi, A.L.; Kasampalis, D.A.; Moshou, D. Application of Multilayer Perceptron with Automatic Relevance Determination on Weed Mapping Using UAV Multispectral Imagery. Sensors 2017, 17, 2307. [CrossRef] 30. Moshou, D.; Pantazi, X.E.; Alexandridis, T.; Bravo, C.; Whetton, R.; Mouazen, A.M. Towards Real Time Weed Detection Using Novelty Detection and UAV Multispectral Imaging. Sensors 2017, 17, 2007. 31. Ibrahim, M.; Akhtar, N.; Wang, H.; Anwar, S.; Mian, A. Multistream Network for LiDAR and Camera-based 3D Object Detection in Outdoor Scenes. In Proceedings of the 2025 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS); IEEE: Piscataway, NJ, USA, 2025; pp. 7796–7803. 32. Ibrahim, M.; Wang, H.; A. Iqbal, I.; Miao, Y.; Albaqami, H.; Blom, H.; Mian, A. Forest stem extraction and modeling (FoSEM): A LiDAR-based framework for accurate tree stem extraction and modeling in radiata pine plantations. Remote Sens. 2025, 17, 445. [CrossRef] 33. Shahi, T.; Howard, C.; McCool, C. Deep Learning Methods for Weed Mapping in Cropping Systems: A Comparative Study. Drones 2023, 7, 439. 34. Sa, I.; Chen, Z.; Popovi´c, M.; McCool, R.I.; Dayoub, F.; Corke, P.; Upcroft, B. WeedMap: A Large-Scale Semantic Weed Mapping Framework Using Aerial Multispectral Imaging and Deep Neural Networks. arXiv 2018, arXiv:1809.08938. [CrossRef] 35. Gupta, A.; Kumar, R.; Sharma, P. Drone-Based Imagery and Deep Learning in Precision Agriculture: A Review. Remote Sens. 2023, 15, 4943. 36. Olsen, A.; Konovalov, D.A.; Philippa, B.; Ridd, P.; Wood, J.C.; Johns, J.; Banks, W.; Girgenti, B.; Kenny, O.; Whinney, J.; et al. DeepWeeds: A Multiclass Weed Species Image Dataset for Deep Learning. Sci. Rep. 2019, 9, 2058. [CrossRef] 37. Dosovitskiy, A.; Beyer, L.; Kolesnikov, A.; Weissenborn, D.; Zhai, X.; Unterthiner, T.; Dehghani, M.; Minderer, M.; Heigold, G.; Gelly, S.; et al. An Image is Worth 16 × 16 Words: Transformers for Image Recognition at Scale. In Proceedings of the International Conference on Learning Representations, Virtual Event, Austria, 3–7 May 2021. 38. Liu, Z.; Lin, Y.; Cao, Y.; Hu, H.; Wei, Y.; Zhang, Z.; Lin, S.; Guo, B. Swin Transformer: Hierarchical Vision Transformer Using Shifted Windows. In Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV), Montreal, BC, Canada, 11–17 October 2021; IEEE: Piscataway, NJ, USA, 2021; pp. 10012–10022. 39. Xie, E.; Wang, W.; Yu, Z.; Anandkumar, A.; Alvarez, J.M.; Luo, P. SegFormer: Simple and Efficient Design for Semantic Segmentation with Transformers. In Proceedings of the Advances in Neural Information Processing Systems, Online, 7 December 2021; Curran Associates, Inc.: Red Hook, NY, USA, 2021. 40. Zuo, X.; Huang, X.; Wang, Y.; Li, J. MSViT: Multi-Scale Vision Transformer for Remote Sensing Image Segmentation. Remote Sens. 2022, 14, 5563. 41. Liu, Y.; Mei, S.; Zhang, S.; Wang, Y.; He, M.; Du, Q. Semantic Segmentation of High-Resolution Remote Sensing Images Using an Improved Transformer. In Proceedings of the 2022 IEEE International Geoscience and Remote Sensing Symposium (IGARSS); IEEE: Piscataway, NJ, USA, 2022; pp. 3496–3499. 42. Li, Z.; Chen, H.; He, X.; Li, Y.; Cheng, G.; Li, X. UNetFormer: A UNet-like Transformer for Efficient Semantic Segmentation of Remote Sensing Images. IEEE Trans. Geosci. Remote Sens. 2023, 61, 1–15. 43. Kong, L.; Ma, L.; Fang, L.; Liu, X. SpectralFormer: Rethinking Hyperspectral Image Classification with Transformers. IEEE Trans. Geosci. Remote Sens. 2022, 60, 1–15. 44. Ahmad, S.; Chen, Z.; Ikram, S.; Ikram, A. AI-Enabled Vision Transformer for Automated Weed Detection: Advancing Innovation in Agriculture. Int. J. Adv. Comput. Sci. Appl. 2024, 15. [CrossRef] 45. Guo, Z.; Cai, D.; Jin, Z.; Xu, T.; Yu, F. Research on unmanned aerial vehicle (UAV) rice field weed sensing image segmentation method based on CNN-transformer. Comput. Electron. Agric. 2025, 229, 109710. [CrossRef] 46. Ma, Y.; Ji, Y.; Cao, J.; Zhang, W. RS3Mamba: Visual State Space Model for Remote Sensing Image Semantic Segmentation. arXiv 2024, arXiv:2404.02457. [CrossRef] 47. Wang, Y.; Cao, L.; Deng, H. MFMamba: A Mamba-Based Multi-Modal Fusion Network for Semantic Segmentation of Remote Sensing Images. Sensors 2024, 24, 7266. [CrossRef] [PubMed]

https://doi.org/10.3390/rs18060915

Remote Sens. 2026, 18, 915 23 of 23

48. Ding, H.; Xia, B.; Liu, W.; Zhang, Z.; Zhang, J.; Wang, X.; Xu, S. A Novel Mamba Architecture with a Semantic Transformer for Efficient Real-Time Remote Sensing Semantic Segmentation. Remote Sens. 2024, 16, 2620. [CrossRef] 49. Cao, Y.; Liu, C.; Wu, Z.; Zhang, L.; Yang, L. Remote Sensing Image Segmentation Using Vision Mamba and Multi-Scale Multi-Frequency Feature Fusion. Remote Sens. 2025, 17, 1390. [CrossRef] 50. Li, F.; Wang, X.; Wang, H.; Karimian, H.; Shi, J.; Zha, G. LMVMamba: A Hybrid U-Shape Mamba for Remote Sensing Segmentation with Adaptation Fine-Tuning. Remote Sens. 2025, 17, 3367. [CrossRef] 51. Zheng, J.; Fu, Y.; Chen, X.; Zhao, R.; Lu, J.; Zhao, H.; Chen, Q. EGCM-UNet: Edge Guided Hybrid CNN-Mamba UNet for Farmland Remote Sensing Image Semantic Segmentation. Geocarto Int. 2025, 40, 2440407. [CrossRef] 52. Li, R.; Ding, X.; Peng, S.; Cai, F. U-MoEMamba: A Hybrid Expert Segmentation Model for Cabbage Heads in Complex UAV Low-Altitude Remote Sensing Scenarios. Agriculture 2025, 15, 1723. [CrossRef] 53. Cohen, J. A Coefficient of Agreement for Nominal Scales. Educ. Psychol. Meas. 1960, 20, 37–46. [CrossRef] 54. Efron, B.; Tibshirani, R.J. An Introduction to the Bootstrap; Chapman & Hall/CRC Monographs on Statistics and Applied Probability; Chapman and Hall/CRC: New York, NY, USA, 1994. 55. PyTorch Contributors. Reproducibility. PyTorch Documentation. 2025. Available online: https://docs.pytorch.org/docs/stable/ notes/randomness.html (accessed on 15 March 2026). 56. Loshchilov, I.; Hutter, F. Decoupled Weight Decay Regularization. In Proceedings of the International Conference on Learning Representations, New Orleans, LA, USA, 6–9 May 2019. 57. Wang, J.; Yang, W.; Zhang, X.; Huang, G.; Qian, J. LoveDA: A Remote Sensing Land-Cover Dataset for Domain Adaptive Semantic Segmentation. arXiv 2021, arXiv:2110.08733. 58. Breiman, L. Random Forests. Mach. Learn. 2001, 45, 5–32. [CrossRef] 59. Zhou, Z.; Siddiquee, M.M.R.; Tajbakhsh, N.; Liang, J. UNet++: A Nested U Net Architecture for Medical Image Segmentation. In Proceedings of the Deep Learning in Medical Image Analysis and Multimodal Learning for Clinical Decision Support; Springer International Publishing: Cham, Switzerland, 2018; pp. 3–11. 60. Chen, L.C.; Papandreou, G.; Schroff, F.; Adam, H. Rethinking Atrous Convolution for Semantic Image Segmentation. arXiv 2017, arXiv:1706.05587. [CrossRef] 61. Zhao, H.; Shi, J.; Qi, X.; Wang, X.; Jia, J. Pyramid Scene Parsing Network. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition; IEEE: Piscataway, NJ, USA, 2017; pp. 2881–2890. 62. Wang, J.; Sun, K.; Cheng, T.; Jiang, B.; Deng, C.; Zhao, Y.; Liu, D.; Mu, Y.; Tan, M.; Wang, X.; et al. Deep High Resolution Representation Learning for Visual Recognition. IEEE Trans. Pattern Anal. Mach. Intell. 2020, 43, 3349–3364. [CrossRef] 63. Yu, C.; Gao, J.; Wang, C.; Yu, G.; Shen, C.; Sang, N. BiSeNet V2: Bilateral Network with Guided Aggregation for Real Time Semantic Segmentation. Int. J. Comput. Vis. 2021, 129, 3051–3072. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.

https://doi.org/10.3390/rs18060915
