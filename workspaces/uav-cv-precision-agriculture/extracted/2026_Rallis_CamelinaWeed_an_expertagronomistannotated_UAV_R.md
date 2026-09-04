---
workspace_id: SCI-000877
doi: 10.1016/j.dib.2026.113135
title: 'CamelinaWeed: an expert-agronomist-annotated UAV RGB and multispectral dataset
  for weed and crop monitoring in'
authors:
- family_name: Rallis
  given_name: Ioannis N
  orcid: null
- family_name: Kempapidis
  given_name: Kyriakos
  orcid: null
- family_name: Raptis
  given_name: Panagiotis
  orcid: null
- family_name: Raptis
  given_name: Emmanuel K
  orcid: null
- family_name: Kapoutsis
  given_name: Athanasios Ch
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:21:25.887816+00:00'
---

# CamelinaWeed: an expert-agronomist-annotated UAV RGB and multispectral dataset for weed and crop monitoring in

Data in Brief 68 (2026) 113135

Contents lists available at ScienceDirect

Data in Brief

journal homepage: www.elsevier.com/locate/dib

Data Article

CamelinaWeed: an  expert-agronomist-annotated UAV RGB and  multispectral dataset for weed and crop  monitoring in Camelina sativa

Ioannis N. Rallis a , c , ∗, Kyriakos Kempapidis b , Panagiotis Raptis c ,  Emmanuel K. Raptis a , Athanasios Ch. Kapoutsis a , d

a Department of Electrical and Computer Engineering, Democritus University of Thrace, Xanthi, Greece  b BIOS Agrosystems SA, Sindos Industrial Area, Thessaloniki, Greece  c Information Technologies Institute, Centre for Research and Technology Hellas (CERTH), Thessaloniki, Greece  d Athena Research Center, Institute for Language and Speech Processing, Xanthi, Greece

a b s t r a c t

a r t i c l e  i n f o

This dataset provides UAV-based RGB and multispectral im-  agery for crop monitoring, weed mapping, and ﬁeld-level  analysis in Camelina sativa cultivation. Data were collected  from three agricultural ﬁelds in Thessaloniki and Chalkidiki,  Greece, during summer 2025 and winter 2025–2026, captur-  ing variability across locations, seasons, crop growth stages,  UAV platforms, ﬂight altitudes, spatial resolutions, illumina-  tion conditions, and sensing modalities. The dataset includes  3023 manually annotated RGB UAV images with human  expert-generated polygon annotations of weed instances. The  annotation scheme includes both coarse weed categories,  such as broadleaf, narrowleaf, and generic weed classes,  and ﬁne-grained species-level labels, supporting classiﬁca-  tion, object detection, semantic and instance segmentation,  hierarchical learning, and weed distribution analysis. In ad-  dition, the dataset provides RGB and multispectral UAV im-  agery, the raw RGB and multispectral images used for or-  thomosaic reconstruction, and both RGB and multispectral  orthomosaic products in GeoTIFF format. The data were ac-

Article history:  Received 27 May 2026  Revised 28 July 2026  Accepted 30 July 2026  Available online 5 August 2026

Dataset link: CamelinaWeed: Annotated  UAV Imagery Dataset for Camelina sativa  (Original data)

Keywords:  Precision agriculture  Weed mapping  Remote sensing  Computer vision  Semantic segmentation

∗Corresponding author at: Department of Electrical and Computer Engineering, Democritus University of Thrace, Xan-  thi, Greece.

E-mail address: irallis@ee.duth.gr (I.N. Rallis).

https://doi.org/10.1016/j.dib.2026.113135  2352-3409/© 2026 The Author(s). Published by Elsevier Inc. This is an open access article under the CC BY license  ( http://creativecommons.org/licenses/by/4.0/ )

2  I.N. Rallis, K. Kempapidis and P. Raptis et al. / Data in Brief 68 (2026) 113135

quired using DJI Phantom 4 Pro and DJI Mavic 3 M UAV  platforms at different ﬂight altitudes, resulting in multi-  ple ground sampling distances and image resolutions. This  dataset is intended to support the development, benchmark-  ing, and validation of computer vision and precision agricul-  ture methods under realistic ﬁeld conditions. To the best of  our knowledge, it is among the ﬁrst publicly available UAV  datasets speciﬁcally focused on weed monitoring and ﬁeld  analysis in Camelina sativa crops.

© 2026 The Author(s). Published by Elsevier Inc.  This is an open access article under the CC BY license

( http://creativecommons.org/licenses/by/4.0/ )

Speciﬁcations Table

Subject  Computer Sciences  Speciﬁc subject area  UAV-based remote sensing and precision agriculture in Camelina sativa ﬁelds  Type of data  Annotated and Raw RGB images (JPEG)  Raw multispectral images (TIFF)  Orthomosaics (GeoTIFF)  Polygon annotations (JSON)  Data collection  Data were collected using a DJI Phantom 4 Pro UAV equipped with an RGB camera and  a DJI Mavic 3 M equipped with RGB and multispectral cameras. Images were collected  during UAV coverage missions over Camelina sativa ( L. ) Crantz ﬁelds, with the camera  gimbal adjusted to −89 ° vertically to the ﬁeld. Image acquisition was performed at  ﬂight altitudes of 2 m, 3 m, 5 m, and 10 m, depending on the ﬁeld and UAV platform.  The dataset includes data collected from three agricultural ﬁelds in Thessaloniki and  Chalkidiki, Greece, during summer and winter cultivation periods.  Data source location  Winter cultivation ﬁeld (Thessaloniki, Greece):  [40.766551, 22.993202; 40.766327, 22.994137; 40.767043, 22.994564; 40.767380,  22.993470]  Winter cultivation ﬁeld (Chalkidiki, Greece):  [40.36 8424, 23.06 8174; 40.36 8555, 23.069137; 40.369965, 23.068723; 40.369791,  23.067736]  Summer cultivation ﬁeld (Thessaloniki, Greece):  [40.565772, 22.990067; 40.566154, 22.991342; 40.568324, 22.989971; 40.567646,  22.988174; 40.566623, 22.988909]  Data accessibility  Repository name: Zenodo  Data identiﬁcation number: https://doi.org/10.5281/zenodo.20148697  Direct URL to data: https://zenodo.org/records/20148697  Instructions for accessing these data:  The complete dataset is publicly available through the Zenodo repository. Dataset  documentation, annotation details, directory structure, and visualization tools are  additionally provided through the public GitHub repository:  https://github.com/aura-laboratory/  CamelinaWeed-Annotated-UAV-Imagery-Dataset-for-Camelina-sativa  Related research article  None


## 1. Value of the Data

• The dataset ﬁlls a gap in the literature by providing UAV imagery from Camelina sativa ﬁelds,  offering exam ples for training and testing automated weed detection models in this under-  represented crop.  • The dataset was collected under real ﬁeld conditions using UAV platforms, includes EXIF  metadata, and was acquired at different ﬂight altitudes, supporting precision agriculture ap-  plications, simulation studies for autonomous agricultural robots, and the evaluation of scale  variation across spatial resolutions.

I.N. Rallis, K. Kempapidis and P. Raptis et al. / Data in Brief 68 (2026) 113135 3

• Data acquired from multiple ﬁelds in Chalkidiki and Thessaloniki and across different seasons  (summer and winter) enable the study of model generalization under varying environmen-  tal conditions, crop growth stages, and illumination, as well as potential variations in weed  distribution.  • The annotations include both generic categories (e.g., broadleaf, narrowleaf, weed) and more  detailed subclasses, enabling ﬂexible use of the dataset for different levels of analysis.  • The dataset supports classiﬁcation, detection, segmentation, and hierarchical learning tasks,  while also enabling downstream applications such as automated weeding, crop monitoring,  yield protection, and decision-support systems for more sustainable agricultural manage-  ment.


## 2. Background

Camelina sativa is an emerging oilseed crop of increasing interest in sustainable agriculture  and is recognized in North America and Europe as a low-input crop with valuable applications  [ 1–3 ]. However, weed management remains a major challenge for its successful commercial pro-  duction [ 4 ], highlighting the need for effective weed monitoring during cultivation. The dataset  was compiled to provide UAV-based RGB and multispectral imagery from Camelina sativa ﬁelds  under real agricultural conditions. Data were collected from ﬁelds in Thessaloniki and Chalkidiki,  Greece, during summer and winter cultivation periods, using different UAV platforms, ﬂight al-  titudes, spatial resolutions, and sensing modalities. The dataset documents crop and weed vari-  ability at both image and ﬁeld scale, including annotated RGB images for weed detection and  segmentation, raw RGB and MS (multispectral) imagery, and orthomosaic products for broader  ﬁeld-level analysis.

As summarized in Table 1 , existing public UAV crop–weed datasets primarily focus on cotton,  sugar beet, and maize and generally provide either broad crop–weed labels, a limited number of  weed species, or restricted variability in acquisition conditions. At the same time, recent multi-  scale and context-aware aerial-image studies [ 5 , 6 ] emphasize the importance of data that cap-  ture variations in object scale, local detail, and broader scene context. To the best of our knowl-  edge, CamelinaWeed is among the ﬁrst public UAV datasets speciﬁcally developed for weed  monitoring in Camelina sativa . It addresses this research gap by combining expert polygon an-  notations, hierarchical broadleaf, narrowleaf, and species-level labels, naturally imbalanced weed  distributions, weed-positive and weed-negative images, and RGB and multispectral imagery ac-  quired across multiple ﬁelds, seasons, UAV platforms, ﬂight altitudes, and spatial resolutions.  These characteristics provide a dedicated benchmark for evaluating weed detection, segmenta-  tion, hierarchical learning, and multi-scale or context-aware methods under realistic agricultural  conditions.


## 3. Data Description

The presented dataset captures weed occurrences in Camelina sativa crops across three agri-  cultural ﬁelds in Chalkidiki and Thessaloniki, Greece. It was compiled to provide a targeted UAV


> **Table 1**

> Compact comparison of representative publicly available UAV crop-weed datasets.

Dataset  Crop / sensor  Dataset size  Acquisition diversity

CoFly-WeedDB [ 7 ]  Cotton / RGB  201 images  One location; one campaign  WeedMap [ 8 ]  Sugar beet / MS  8 orthomosaics  Two locations; two campaigns  PhenoBench [ 9 ]  Sugar beet / RGB  2872 images  Multiple acquisition dates  WeedsGalore [ 10 ]  Maize / RGB–MS  156 tiles; 4  orthomosaics

Four acquisition dates

CamelinaWeed [ 11 ]  Camelina sativa /  RGB–MS

3023 annotated  images


## 3 ﬁelds; 2 seasons; 2 UAVs;

multiple altitudes and GSDs

4  I.N. Rallis, K. Kempapidis and P. Raptis et al. / Data in Brief 68 (2026) 113135


> **Table 2**

> Summary of the acquired UAV data for orthomosaic generation.

Season  Location  Acquisition setting  Images  Orthomosaic

Winter  2025–2026  Thessaloniki  Mavic 3 M ﬂight at 20 m  altitude RGB

227  ✔

Mavic 3 M ﬂight at 20 m  altitude MS

908  ✔

Winter  2025–2026  Chalkidiki  Mavic 3 M ﬂight at 20 m  altitude RGB

1351  ✔

Mavic 3 M ﬂight at 20 m  altitude MS

5404  ✔


> **Table 3**

> Summary of the acquired UAV data for weed detection.

Season  Location  Acquisition setting  Weed-positive  images

Weed-negative  images

Summer 2025  Thessaloniki  Phantom ﬂight at 5 m  altitude

34  32

Phantom ﬂight at 10 m  altitude

297  46

Winter  2025–2026  Thessaloniki  Phantom ﬂight at 3 m  altitude

17  32

Mavic 3 M ﬂight 1 at  2 m altitude  627  215

Mavic 3 M ﬂight 1 at  2 m altitude MS  − 842

Mavic 3 M ﬂight 2 at  2 m altitude  47  193

Mavic 3 M ﬂight 2 at  2 m altitude MS  − 240

Winter  2025–2026  Chalkidiki  Phantom ﬂight at 3 m  altitude

43  159

Phantom ﬂight at 5 m  altitude

55  144

image dataset for Camelina sativa cultivation, supporting the development of automated weed  detection approaches and providing a practical resource for ﬁeld management and crop mon-  itoring. Data were collected during two distinct time periods, namely summer 2025 and win-  ter 2025–2026, corresponding to different cultivation stages and growing conditions, with the  Camelina sativa crop maintaining healthy growth conditions throughout the acquisition period.

The dataset includes annotated RGB UAV images in JPEG format, polygon-based annotation  ﬁles in JSON format, raw RGB and multispectral imagery, and orthomosaic products in GeoTIFF  format. The annotations include both generic weed categories and species-level labels, support-  ing weed detection, classiﬁcation, and segmentation tasks. The acquired UAV data are summa-  rized in Tables 2 and 3 .


> **Table 2 provides an overview of the UAV data that can be used for orthomosaic generation**

> tasks. These data include both RGB and multispectral imagery together with the correspond- 
ing orthomosaic products generated from the 20 m ﬂights. The raw images in this table were 
used for orthomosaic creation and were not annotated for weed detection. Therefore, they pro- 
vide complementary spatial information for large-scale ﬁeld analysis and visualization of weed 
distribution patterns across the examined agricultural areas.


> **Table 3 summarizes the UAV data that can be used for weed detection tasks. The dataset**

> contains 3023 UAV images, including 1120 images with visible weed presence and 1903 im- 
ages where no weeds were identiﬁed. Weed instances were manually annotated by expert 
agronomists using polygon-based segmentation in the Roboﬂow platform [ 12 ]. The annota- 
tions include both species-level labels and broader categories, such as broadleaf and narrowleaf

I.N. Rallis, K. Kempapidis and P. Raptis et al. / Data in Brief 68 (2026) 113135 5

Fig. 1. Hierarchical organization of weed instances in the dataset. Weed samples are grouped into Broadleaf and Nar-  rowleaf categories, with each terminal node representing a weed species or generic weed group together with the cor-  responding number of instances.

weeds, as illustrated in Fig. 1 . This hierarchical annotation structure enables analysis at different  levels of detail, ranging from general weed classiﬁcation to ﬁne-grained species recognition.

All images in the dataset were acquired using different UAV platforms, resulting in vary-  ing spatial resolutions. Images captured with the DJI Phantom 4 Pro have a resolution of  5472 × 3078 pixels, while images acquired with the DJI Mavic 3 M have a resolution of  1920 × 1080 pixels. This variability enables the evaluation of models under different spatial  scales, acquisition settings, and sensing modalities.

The dataset includes annotated weed instances organized into two main categories, as shown  in Fig. 1 : broadleaf and narrowleaf weeds. The broadleaf group contains seven species-level  classes, while the narrowleaf group includes one generic narrowleaf class and four species-level  classes. This hierarchical organization enables experiments at different levels of classiﬁcation  granularity. The number of annotated instances varies across categories and species, reﬂecting  the natural occurrence of weeds in the examined ﬁelds. This class imbalance should therefore  be considered during model training and evaluation.

As illustrated in Fig. 2 , the annotations were generated using the Roboﬂow platform [ 12 ].  Polygonal annotations were preferred over simpler approaches, such as bounding boxes, because  weed instances often exhibit irregular shapes, overlapping leaves, variable sizes, and complex  spatial distributions. This annotation strategy provides a more precise representation of weed  boundaries, making the dataset suitable for semantic segmentation, weed detection, and ﬁne-  grained analysis tasks.

6  I.N. Rallis, K. Kempapidis and P. Raptis et al. / Data in Brief 68 (2026) 113135

Fig. 2. Example of the annotation format used in the dataset within Roboﬂow. The ﬁrst image presents the raw UAV-  acquired image, while the second image shows the polygon-based annotations visualized in the Roboﬂow environment,  with the corresponding class labels displayed.


> **Table 4**

> Summary of unmanned aerial vehicle and camera speciﬁcations.

Unmanned Aerial  Vehicle

Characteristics

DJI Phantom 4 Pro  RGB Camera: 1-inch CMOS; effective pixels: 20 MP; FOV: 84 degrees; 8.8 mm  / 24 mm (35 mm format equivalent); f/2.8-f/11; autofocus at 1 m-inﬁnity.  DJI Mavic 3M  RGB Camera: 4/3 CMOS; effective pixels: 20 MP; FOV: 84 degrees; 24 mm  equivalent focal length; aperture: f/2.8-f/11; focus: 1 m-inﬁnity.  Multispectral Camera: 1/2.8-inch CMOS; effective pixels: 5 MP; FOV: 73.91  degrees (61.2 degrees x 48.10 degrees); 25 mm equivalent focal length;  aperture: f/2.0; ﬁxed focus.  Bands: Green (G): 560 ± 16 nm; Red (R): 650 ± 16 nm; Red Edge (RE):  730 ± 16 nm; Near Infrared (NIR): 860 ± 26 nm.

Overall, the dataset captures variability across ﬁelds, seasons, UAV platforms, spatial reso-  lutions, acquisition settings, and sensing modalities. This diversity increases the realism of the  dataset and supports the evaluation of weed detection and segmentation approaches under con-  ditions closer to real agricultural deployment.


## 4. Experimental Design, Materials and Methods

For the collection of the dataset, multiple UAV acquisition scenarios were conducted in the  examined agricultural ﬁelds in Thessaloniki and Chalkidiki. The acquisition protocol was de-  signed to include two complementary types of UAV ﬂights: (i) orthomosaic-oriented ﬂights, aim-  ing at the complete coverage and reconstruction of the surveyed ﬁelds, and (ii) low-altitude im-  age acquisition ﬂights, aiming at the detailed image-based recording of individual plants and  weed occurrences under different spatial resolutions and imaging conditions. The acquisitions  were performed using two UAV platforms, namely the DJI Phantom 4 Pro equipped with an RGB  camera and the DJI Mavic 3 M equipped with both RGB and multispectral (MS) cameras. The  main camera characteristics and sensor speciﬁcations of the UAV platforms are summarized in  Table 4 .

For the orthomosaic acquisitions, an autonomous UAV navigation framework was employed  to ensure full coverage of the surveyed ﬁelds. The ﬂight paths were generated using a cover-  age path planning approach based on a spanning tree algorithm [ 13 ], while considering UAV-  speciﬁc parameters such as camera characteristics, platform dimensions, GSD, frontlap, and side-  lap. These orthomosaic ﬂights were performed in both Thessaloniki and Chalkidiki with the DJI  Mavic 3 M at 20 m altitude, using both RGB and MS cameras. As reported in Table 5 , the ﬂights

I.N. Rallis, K. Kempapidis and P. Raptis et al. / Data in Brief 68 (2026) 113135 7


> **Table 5**

> Summary of UAV ﬂight parameters for the data for orthomosaic generation.

Location  Acquisition setting  Drone  Camera  GSD  (cm/pixel)

Frontlap  (%)

Sidelap  (%)

Thessaloniki  Mavic 3 M ﬂight at  20 m altitude RGB  Mavic 3M  RGB  0.5  85  70

Mavic 3 M ﬂight at  20 m altitude MS  Mavic 3M  MS  0.5  85  70

Chalkidiki  Mavic 3 M ﬂight at  20 m altitude RGB  Mavic 3M  RGB  0.5  85  70

Mavic 3 M ﬂight at  20 m altitude MS  Mavic 3M  MS  0.5  85  70

Fig. 3. UAV-based data acquisition workﬂow. The ﬁrst image illustrates the planned coverage path used for autonomous  navigation of the DJI Mavic 3 M over the agricultural ﬁeld in Chalkidiki, while the second image presents the resulting  orthomosaic constructed from the captured images along the ﬂight trajectory.

were planned with a GSD of 0.5 cm/pixel, 85% frontlap, and 70% sidelap. Fig. 3 illustrates both  the planned coverage path followed during the UAV ﬂight and the resulting orthomosaic gener-  ated after image stitching. The deployed UAV coverage path planning software is publicly avail-  able at https://choosepath.org/ .

In addition to the orthomosaic ﬂights, several low-altitude UAV ﬂights, whose acquisition pa-  rameters are summarized in Table 6 , were performed to acquire detailed RGB and MS imagery  of the plants at different spatial resolutions. During the summer 2025 acquisition campaign in  Thessaloniki, two UAV ﬂights were conducted at altitudes of 5 m and 10 m using the DJI Phan-  tom 4 Pro. RGB images were acquired at a ﬂight speed of 3 m/s, while the camera was oriented  at approximately −89 ° with respect to the ground in order to capture a near-vertical ﬁeld of  view. These ﬂights resulted in GSD values of 0.14 cm/pixel and 0.27 cm/pixel for the 5 m and  10 m ﬂights, respectively, with 70% frontlap and 1% sidelap.  During the winter 2025–2026 acquisition campaign in Chalkidiki, the same UAV platform was  used to perform two additional RGB ﬂights at altitudes of 3 m and 5 m, under similar acquisition  settings. These ﬂights resulted in GSD values of 0.08 cm/pixel and 0.14 cm/pixel. In Thessaloniki,  an additional DJI Phantom 4 Pro ﬂight was carried out at an altitude of 3 m, maintaining the  same imaging characteristics and resulting in a GSD of 0.08 cm/pixel. Furthermore, two addi-

8  I.N. Rallis, K. Kempapidis and P. Raptis et al. / Data in Brief 68 (2026) 113135


> **Table 6**

> Summary of UAV ﬂight parameters for the data for weed detection.

Location  Acquisition setting  Drone  Camera  GSD  (cm/pixel)

Thessaloniki  Phantom ﬂight at 5 m  altitude

Phantom 4 Pro  RGB  0.14

Phantom ﬂight at 10 m  altitude

Phantom 4 Pro  RGB  0.27

Phantom ﬂight at 3 m  altitude

Phantom 4 Pro  RGB  0.08

Mavic 3 M ﬂight 1 at  2 m altitude  Mavic 3M  RGB  0.15

Mavic 3 M ﬂight 1 at  2 m altitude MS  Mavic 3M  MS  0.15

Mavic 3 M ﬂight 2 at  2 m altitude  Mavic 3M  RGB  0.15

Mavic 3 M ﬂight 2 at  2 m altitude MS  Mavic 3M  MS  0.15

Chalkidiki  Phantom ﬂight at 3 m  altitude

Phantom 4 Pro  RGB  0.08

Phantom ﬂight at 5 m  altitude

Phantom 4 Pro  RGB  0.14

Fig. 4. Visual diversity of the UAV image dataset, illustrating variations in season, location, crop growth stage, soil back-  ground, and weed presence in Camelina sativa cultivation.

tional low-altitude ﬂights were conducted over different parts of the Thessaloniki ﬁeld using the  DJI Mavic 3 M at an altitude of 2 m, with the gimbal angle adjusted to approximately −89 ° For  each of these Mavic 3 M ﬂights, both RGB and MS images were acquired, resulting in a GSD of  0.15 cm/pixel.  Overall, the acquisition protocol was designed to capture weed occurrences under diverse  seasonal conditions, ﬂight altitudes, ﬁeld environments, and sensing modalities. The summer  acquisitions were performed at relatively higher altitudes, as the crop was closer to harvest,  while the winter acquisitions were conducted at lower altitudes to better capture weed instances  during the early crop growth stages, as shown in Fig. 4 .

4.1. Dataset evaluation

The CamelinaWeed dataset [ 11 ] was evaluated using an NVIDIA GeForce RTX 5060 Ti GPU  with 16 GB VRAM. To prevent data leakage, complete UAV ﬂights were assigned exclusively to  the training, validation, or geographically held-out test subset before tiling. The training sub-  set contained 975 weed-positive and 149 weed-negative images, corresponding to approximately  15% of the positive images, and included the Thessaloniki Phantom ﬂights conducted at 3, 5, and  10 m together with Mavic 3 M Flight 1, while Mavic 3 M Flight 2 was used for validation and the  two Chalkidiki Phantom ﬂights were reserved for testing. Weed-negative images were included

I.N. Rallis, K. Kempapidis and P. Raptis et al. / Data in Brief 68 (2026) 113135 9


> **Table 7**

> Class-wise performance of the object-detection models on the geographically held-out test set.

Model  Class  Precision  Recall  F1-score  AP@50  AP@50–95  Processing  time  (ms/tile)

RT-DETR-L [ 14 ]  Broadleaf  0.846  0.813  0.829  0.792  0.710  9.20  Narrowleaf  0.878  0.821  0.849  0.841  0.723  9.18  Macro  average

0.862  0.817  0.839  0.817  0.717  9.19

YOLO26m [ 15 ]  Broadleaf  0.809  0.701  0.751  0.771  0.630  6.31  Narrowleaf  0.824  0.784  0.804  0.835  0.670  6.30  Macro  average

0.817  0.743  0.777  0.803  0.650  6.30

YOLO26n [ 15 ]  Broadleaf  0.731  0.649  0.688  0.721  0.550  4.20  Narrowleaf  0.811  0.724  0.765  0.774  0.590  4.21  Macro  average

0.771  0.687  0.726  0.748  0.570  4.20

Faster R-CNN  ResNet-50-FPN  [ 16–18 ]

Broadleaf  0.782  0.669  0.721  0.730  0.510  19.00  Narrowleaf  0.811  0.745  0.777  0.760  0.580  19.00  Macro  average

0.797  0.707  0.749  0.745  0.545  19.00


> **Table 8**

> Class-wise mask performance of the YOLO26n-seg instance-segmentation baseline on the geographically held-out test 
set.

Model  Class  Mask  Precision

Mask  Recall

Mask  F1-score

Mask  AP@50

Mask  AP@50–95

Processing  time  (ms/tile)

YOLO26n-seg  [ 15 ]

Broadleaf  0.740  0.630  0.681  0.664  0.490  3.30  Narrowleaf  0.790  0.680  0.731  0.748  0.510  3.30  Macro  average

0.765  0.655  0.706  0.706  0.500  3.30

to expose the models to representative background conditions and reduce false-positive detec-  tions, while their number was limited to prevent background-only samples from dominating the  training process. For object detection, the bounding box associated with each polygon annotation  was converted from [x, y, width, height ] to normalized coordinates [xcenter , ycenter , width, height ] using  the image dimensions. RT-DETR-L [ 14 ], YOLO26m [ 15 ], YOLO26n [ 15 ], and Faster R-CNN with a  ResNet-50-FPN backbone [ 16–18 ] were trained to detect broadleaf and narrowleaf weeds using  768 × 768 image tiles.  As shown in Table 7 , RT-DETR-L achieved the highest macro performance, with a Precision  of 0.862, Recall of 0.817, F1-score of 0.839, AP@50 of 0.817, and AP@50–95 of 0.717. YOLO26m  achieved a comparable AP@50 of 0.803 with a processing time of 6.30 ms per tile, compared  with 9.19 ms for RT-DETR-L. YOLO26n was the fastest detector at 4.20 ms per tile. Processing  time represents the average time required for preprocessing and model inference on a single  768 × 768 tile using the GPU. Narrowleaf weeds achieved higher class-speciﬁc performance than  broadleaf weeds across all evaluated models.

A separate instance-segmentation experiment was conducted using the same ﬂight-wise split  and the original polygon annotations. As shown in Table 8 , YOLO26n-seg [ 15 ] achieved a macro  mask Precision of 0.765, Recall of 0.655, F1-score of 0.706, AP@50 of 0.706, and AP@50–95 of  0.500. Overall, the evaluation demonstrates the practical usability of the dataset for training and  evaluating different representative state-of-the-art weed-detection and instance-segmentation  models.

10  I.N. Rallis, K. Kempapidis and P. Raptis et al. / Data in Brief 68 (2026) 113135

Limitations

The dataset was collected from three agricultural ﬁelds located in Thessaloniki and Chalkidiki,  Greece, and therefore reﬂects the environmental and cultivation conditions of these speciﬁc re-  gions. Weed distributions and species frequencies are naturally imbalanced across the annotated  categories, resulting in unequal representation of weed classes. In addition, the dataset was ac-  quired using speciﬁc UAV platforms, ﬂight altitudes, and sensing conﬁgurations, which may in-  ﬂuence the direct generalization of models trained on the dataset to substantially different ac-  quisition conditions or agricultural environments.

Ethics Statement

The authors have read and followed the ethical requirements for publication in Data in Brief.  The current work does not involve human subjects, animal experiments, or data collected from  social media platforms. UAV operations were carried out under the applicable European Union  and national regulations governing unmanned aircraft ﬂights.

Ethics Declaration

The author(s) declare(s) that the study does not involve humans nor animal subjects.

Data Availability

CamelinaWeed: Annotated UAV Imagery Dataset for Camelina sativa (Original data) (Zenodo).

CRediT Author Statement

Ioannis N. Rallis: Conceptualization, Data curation, Investigation, Software, Visualization,  Writing – original draft; Kyriakos Kempapidis: Data curation, Formal analysis, Investigation,  Validation; Panagiotis Raptis: Writing – review & editing, Formal analysis, Investigation, Vali-  dation; Emmanuel K. Raptis: Conceptualization, Data curation, Investigation, Software, Visual-  ization, Writing – original draft, Supervision; Athanasios Ch. Kapoutsis: Conceptualization, Su-  pervision, Project administration, Writing – review & editing.

Acknowledgements

This research was funded by the European Union – NextGenerationEU and national resources  through the Recovery and Resilience Facility (RRF) under the “Clusters of Research Excellence – CREs” Action of the National Recovery and Resilience Plan “Greece 2.0” (project code: ϒ3TA-  0559722 ).

Declaration of Competing Interest

The authors declare that they have no known competing ﬁnancial interests or personal rela-  tionships that could have appeared to inﬂuence the work reported in this paper.

I.N. Rallis, K. Kempapidis and P. Raptis et al. / Data in Brief 68 (2026) 113135 11


## References

[1] M. Mondor , A.J. Hernández-Álvarez , Camelina sativa composition, attributes, and applications: a review, Eur. J. Lipid

Sci. Technol. 124 (2022) 210 0 035 .  [2] F. Zanetti , A. Monti , M.T. Berti , Challenges and opportunities for new industrial oilseed crops in EU-27: a review,

Ind. Crops. Prod. 50 (2013) 580–595 .  [3] C.J. Zhang , Y. Gao , C. Jiang , L. Liu , Y. Wang , D.S. Kim , J. Yu , L. Yu , F. Li , Y. Fan , et al. , Camelina seed yield and quality

in different growing environments in northern China, Ind. Crops. Prod. 172 (2021) 114071 .  [4] S.Z. Dai, Y. Wang, M.J. Yook, H.Z. Wu, M. Chen, C.J. Zhang, Screening of pre- and post-emergence herbicides for

weed control in Camelina sativa (L.) Crantz, Agronomy 15 (2025) 640, doi: 10.3390/agronomy15030640 .  [5] S.D. Khan , S. Basalamah , Multi-scale and context-aware framework for ﬂood segmentation in post-disaster high

resolution aerial images, Remote Sens. (Basel) 15 (8) (2023) 2208 .  [6] S.D. Khan , S. Basalamah , Multi-branch deep learning framework for land scene classiﬁcation in satellite imagery,

Remote Sens. (Basel) 15 (13) (2023) 3408 .  [7] M. Krestenitis , E.K. Raptis , A.C. Kapoutsis , K. Ioannidis , E.B. Kosmatopoulos , S. Vrochidis , I. Kompatsiaris , CoFly-

-WeedDB: a UAV image dataset for weed detection and species identiﬁcation, Data Brief. 45 (2022) 108575 .  [8] I. Sa , M. Popovi´c , R. Khanna , Z. Chen , P. Lottes , F. Liebisch , J. Nieto , C. Stachniss , A. Walter , R. Siegwart , WeedMap:

a large-scale semantic weed mapping framework using aerial multispectral imaging and deep neural network for  precision farming, Remote Sens. (Basel) 10 (9) (2018) 1423 .  [9] J. Weyler , F. Magistri , E. Marks , Y.L. Chong , M. Sodano , G. Roggiolani , N. Chebrolu , C. Stachniss , J. Behley , Phe-

nobench: a large dataset and benchmarks for semantic image interpretation in the agricultural domain, IEEe Trans.  Pattern. Anal. Mach. Intell. 46 (12) (2024) 9583–9594 .  [10] E. Celikkan , T. Kunzmann , Y. Yeskaliyev , S. Itzerott , N. Klein , M. Herold , WeedsGalore: a multispectral and multi-

temporal UAV-based dataset for crop and weed segmentation in agricultural maize ﬁelds, in: 2025 IEEE/CVF Winter  Conference on Applications of Computer Vision (WACV), IEEE, 2025 Feb 26, pp. 4767–4777 .  [11] I.N. Rallis, K. Kempapidis, P. Raptis, E.K. Raptisand, A. Kapoutsis, CamelinaWeed: annotated UAV imagery dataset for

Camelina sativa, Zenodo (2026) May 19, doi: 10.5281/zenodo.20148697 .  [12] Roboﬂow, 2026. Roboﬂow annotation and computer vision platform. Available online: https://roboﬂow.com/

(accessed .  [13] Y. Gabriely , E. Rimon , Spanning-tree based coverage of continuous areas by a mobile robot, Ann. Math. Artif. Intell.

31 (2001) 77–98 .  [14] Y. Zhao , W. Lv , S. Xu , J. Wei , G. Wang , Q. Dang , Y. Liu , J. Chen , Dets beat yolos on real-time object detection, in:

Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2024, pp. 16965–16974 .  [15] G. Jocher , J. Qiu , M. Liu , S. Lyu , F.C. Akyon , M.E. Kalfaoglu , Ultralytics YOLO26: uniﬁed real-time end-to-end vision

models, arXiv preprint (2026 Jun 2) arXiv:2606.03748 .  [16] S. Ren , K. He , R. Girshick , J. Sun , Faster R-CNN: towards real-time object detection with region proposal networks,

IEEe Trans. Pattern. Anal. Mach. Intell. 39 (6) (2016) 1137–1149 .  [17] M. Shaﬁq , Z. Gu , Deep residual learning for image recognition: a survey, Appl. Sci. 12 (18) (2022) 8972 .  [18] T.Y. Lin , P. Dollár , R. Girshick , K. He , B. Hariharan , S. Belongie , Feature pyramid networks for object detection, in:

Proceedings of the IEEE conference on computer vision and pattern recognition, 2017, pp. 2117–2125 .
