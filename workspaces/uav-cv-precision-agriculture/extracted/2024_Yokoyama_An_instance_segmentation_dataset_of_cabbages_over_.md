---
workspace_id: SCI-000902
doi: 10.1016/j.dib.2024.110699
title: An instance segmentation dataset of cabbages over the whole growing season
  for UAV imagery.
authors:
- family_name: Yokoyama
  given_name: Yui
  orcid: null
- family_name: Matsui
  given_name: Tsutomu
  orcid: null
- family_name: Tanaka
  given_name: Takashi S T
  orcid: null
year: 2024
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:21:26.023459+00:00'
---

# An instance segmentation dataset of cabbages over the whole growing season for UAV imagery.

Data in Brief 55 (2024) 110699

Contents lists available at ScienceDirect

Data in Brief

journal homepage: www.elsevier.com/locate/dib

Data Article

An instance segmentation dataset of cabbages  over the whole growing season for UAV  imagery

Yui Yokoyama a , Tsutomu Matsui b , Takashi S.T. Tanaka b , c , d , ∗

a Graduate School of Natural Science and Technology, Gifu University, 1-1 Yanagido, Gifu City 501-1193, JAPAN  b Faculty of Applied Biological Sciences, Gifu University, 1-1 Yanagido, Gifu City 501-1193, JAPAN  c Artiﬁcial Intelligence Advanced Research Center, Gifu University, 1-1 Yanagido, Gifu City 501-1193, JAPAN  d Department of Agroecology, Faculty of Technical Sciences, Aarhus University, Forsøgsvej 1, 4200 Slagelse, Denmark

a b s t r a c t

a r t i c l e  i n f o

Crop growth monitoring is essential for both crop and supply  chain management. Conventional manual sampling is not  feasible for assessing the spatial variability of crop growth  within an entire ﬁeld or across all ﬁelds. Meanwhile, UAV-  based remote sensing enables the eﬃcient and nondestruc-  tive investigation of crop growth. A variety of crop-speciﬁc  training image datasets are needed to detect crops from UAV  imagery using a deep learning model. Speciﬁcally, the train-  ing dataset of cabbage is limited. This data article includes  annotated cabbage images in the ﬁelds to recognize cabbages  using machine learning models. This dataset contains 458  images with 17,621 annotated cabbages. Image sizes are  approximately 500 to 10 0 0 pixel squares. Since these cab-  bage images were collected from different cultivars during  the whole growing season over the years, deep learning  models trained with this dataset will be able to recognize a  wide variety of cabbage shapes. In the future, this dataset  can be used not only in UAVs but also in land-based robot

Article history:  Received 22 October 2023  Revised 12 March 2024  Accepted 24 June 2024  Available online 29 June 2024

Dataset link: An annotated image dataset  of cabbages for instance segmentation  (Original data)

Keywords:  Annotation  COCO format  Deep learning  Horticulture  Precision agriculture  Remote sensing

∗Corresponding author at: Department of Agroecology, Faculty of Technical Sciences, Aarhus University, Forsøgsvej 1,  4200 Slagelse, Denmark.  E-mail address: takashi@agro.au.dk (T.S.T. Tanaka).  Social media: @SonamTashi331 (T.S.T. Tanaka)

https://doi.org/10.1016/j.dib.2024.110699  2352-3409/© 2024 The Author(s). Published by Elsevier Inc. This is an open access article under the CC BY license  ( http://creativecommons.org/licenses/by/4.0/ )

2  Y. Yokoyama, T. Matsui and T.S.T. Tanaka / Data in Brief 55 (2024) 110699

applications for crop sensing or associated plant-speciﬁc  management.

© 2024 The Author(s). Published by Elsevier Inc.  This is an open access article under the CC BY license

( http://creativecommons.org/licenses/by/4.0/ )

Speciﬁcations Table

Subject  Agronomy and Crop Science  Speciﬁc subject area  Instance segmentation for cabbage by UAV imagery  Data format  Raw, annotated  Type of data  RGB images, Instance segmentation annotations  Data collection  Cabbage images were collected using UAVs in farmers’ ﬁelds over three years  (2020, 2021, and 2022). An orthomosaic process was performed using Pix4D  and images were split into 500 to 10 0 0 pixels square. Cabbage contours were  annotated and exported in a COCO format.  Data source location  Kaizu, Gifu Prefecture, Japan (35 °13′ N 136 °39′ E)  Yoro, Gifu Prefecture, Japan (35 °20′ N 136 °33′ E)  Sunomata, Gifu Prefecture, Japan (35 °21′ N 136 °40′ E)  Data accessibility  Repository name: Mendeley Data  Data identiﬁcation number: 10.17632/5cp2dyjczk.2  Direct URL to data: https://data.mendeley.com/datasets/5cp2dyjczk/2


## 1. Value of the Data

• This dataset was created by object-based annotation of individual cabbage with laborious  manual effort s. The use of distinct dat aset and inst ance segment ation models such as Mask  R-CNN [ 1 ] and YOLACT [ 2 ] enables on-farm assessment of individual cabbage growth (e.g.,  leaf area index and biomass) by quantifying individual cabbage contours.  • This dataset can also be used for object detection such as YOLO [ 3 ] because the JSON ﬁle  includes the bounding box data if practitioners only need to count the number of cabbages.  • The dataset is highly complementary to the existing dataset [ 4 , 5 ] because it consists of multi-  ple cultivars with different morphological traits, and the images were taken during the whole  growing season. Since the image data is classiﬁed by cultivar, location and image acquisition  time, it is easy to select a speciﬁc cultivar or growing season depending on the purpose of  model optimisation and validation.  • The dataset can be used for actual crop monitoring. In the future, it is expected to enable  automatic plant-level management coupled with land-based agricultural robots.


## 2. Data Description

The dataset includes 458 annotated RGB images and an associated JSON ﬁle in COCO format.  The JSON ﬁle contains 17,621 annotated masks of cabbages in the images. Images are placed in  three levels of subfolders. Each subfolder represents the cultivar, location and image acquisition  timing (i.e., year and month), respectively. Accordingly, the locations Kaizu, Sunomata and Yoro  contain 5455, 6524 and 5642 annotated masks, respectively. The number of annotated masks  for cultivars ‘OkinaSP’, ‘Suiryoku’, ‘TCA422’, ‘Yumebutai’ is 7528, 1398, 5376 and 2600, respec-  tively. Meanwhile, cultivars ‘Red cabbage’ and ‘Yumegoromo’ only contain 538 and 181 annotated  masks, respectively.

Each image is named in the format “image(a)_(b)_(c)_(d)_(e).png”.

• (a) Image number  • (b) The day the image was taken  • (c) Location

Y. Yokoyama, T. Matsui and T.S.T. Tanaka / Data in Brief 55 (2024) 110699 3

Fig. 1. Raw and annotated images of the dataset.

• (d) Cultivar name  • (e) Image size

All images have annotated information in a JSON ﬁle “annotated.json”. Fig. 1 shows the seg-  mentation masks of the dataset. Each cabbage mask was enclosed along the outline and saved  as the label name “cabbage”.


## 2. Experimental Design, Materials and Methods

2.1. Field data collection

The RGB images of cabbages were collected in 2020, 2021, and 2022 in farmers’ ﬁelds in  three cities, including Yoro, Sunomata and Kaizu, Gifu Prefecture, Japan. Table 1 shows the cul-

4  Y. Yokoyama, T. Matsui and T.S.T. Tanaka / Data in Brief 55 (2024) 110699


> **Table 1**

> Transplant day of each day and cultivar.

Year  City  Cultivar  Transplant Day

2020  Kaizu  OkinaSP  Aug 30, 2020  2021  Yoro  Sunomata  Kaizu

OkinaSP  Suiryoku  Yumebutai  OkinaSP  TCA422  OkinaSP

Aug 30, 2021  Aug 30, 2021  Aug 30, 2021  Sep 1, 2021  Sep 2, 2021  Aug 30, 2021  2022  Yoro  Sunomata

OkinaSP  Suiryoku  Yumebutai  Red cabbage  OkinaSP  TCA422  Yumegoromo

Aug 29, 2022  Aug 29, 2022  Aug 29, 2022  Aug 29, 2022  Aug 29 and 30,  2022  Aug 29 and 30,  2022  Aug 29 and 30,  2022

tivars grown in each city and transplanting day. In Kaizu on 2020 and 2021, cabbages were cul-  tivated by transplanting one row in a ridge. Others were cultivated by transplanting two rows  in a ridge. This also makes images look different due to the different plant density and trans-  plant spacing. Fertilisation and pest/disease management was performed according to the rec-  ommendation suggested by the local crop advisory service. All the cabbages were grown under  rainfed conditions. During the cabbage growing season from September to December, RGB im-  ages were taken using a UAV. All images were captured between 9:0 0 and 16:0 0 under various  cloud conditions from clear sky to thick clouds. Given the temporally varying light intensity even  within a day and varying sun angles over the growing seasons from summer to winter, entire  dataset covers the effect of a wide range of varying illumination conditions on image quality. In  2020, Phantom4 (DJI, Shenzhen, China) was used for image acquisition at a 20 m altitude with  75% front and side overlap. In 2021 and 2022, the digital camera α6600 (Sony, Tokyo, Japan)  mounted on MATRICE300 (DJI, Shenzhen, China) was used for image acquisition at a 30 m alti-  tude with 70–80% front and side overlap. The coordinates of RGB images were measured using  KlauPPK (Klau Geomatics, New South Wales, Australia) with a 0.03-m accuracy.

2.2. Data preprocessing

The orthomosaic process was performed using Pix4D mapper version 4.6.4 (Pix4D, Prilly,  Switzerland) based on the processing template 3D Maps. The orthomosaic images were split  into 515–10 0 0 pixel squares using GDAL as a Python module. The spatial resolution of the resul-  tant split images ranged from 3.3 to 6.3 mm. A total of 458 split images were randomly selected  from the split images. The cabbage masks were manually annotated using the COCO annotator  [ 6 ]. The drawing tablet Cintiq 16 (Wacom Co., Ltd, Saitama, Japan) was used for the accurate  and eﬃcient annotations. To accurately draw the semantic annotations for the individual cab-  bage, the application of expert judgement derived from experiences in ﬁeld survey becomes in-  dispensable particularly in situations involving the overlapping of multiple cabbages. Therefore,  highly trained technician was involved in the annotation process, and every annotation were  carefully checked by the authors.

Limitations

None.

Y. Yokoyama, T. Matsui and T.S.T. Tanaka / Data in Brief 55 (2024) 110699 5

Ethics Statement

The study does not involve experiments on humans or animals.

Data Availability

An annotated image dataset of cabbages for instance segmentation (Original data) (Mendeley  Data)

CRediT Author Statement

Yui Yokoyama: Conceptualization, Methodology, Data curation, Writing – original draft;  Tsutomu Matsui: Writing – review & editing, Supervision; Takashi S.T. Tanaka: Conceptualiza-  tion, Methodology, Data curation, Writing – review & editing, Supervision.

Acknowledgements

This study was supported by the JST FOREST Programme, Grant Number JPMJFR221C .  We would like to thank Japan Agricultural Cooperative Nishimino and the farmers for their  permission for the ﬁeld surveys.

Declaration of Competing Interest

The authors declare that they have no known competing ﬁnancial interests or personal rela-  tionships that could have appeared to inﬂuence the work reported in this paper.


## References

[1] K. He , G. Gkioxari , P. Dollar , R. Girshick , Mask R-CNN, in: Proceedings of the IEEE International Conference on Com-

puter Vision (ICCV), 2017, pp. 2961–2969 .  [2] D. Bolya , C. Zhou , F. Xiao , Y.J. Lee , YOLACT: real-time instance segmentation, in: Proceedings of the IEEE/CVF Interna-

tional Conference on Computer Vision (ICCV), 2019, pp. 9157–9166 .  [3] J. Redmon , S. Divvala , R. Girshick , A. Farhadi , You only look once: Uniﬁed, real-time object detection, in: Proceedings

of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016, pp. 779–788 .  [4] AI University. 2023. Segmentation cabbage dataset. https://universe.roboﬂow.com/ai-university-0gd1d/segmentation-

cabbage .  [5] J. Clar, Annotated Images of White and Red Cabbage, Zenodo, 2023, doi: 10.5281/zenodo.7961758 .  [6] J. Brooks, coco-annotator. https://github.com/jsbroks/coco-annotator.git , 2019 (accessed 6 October 2023).
