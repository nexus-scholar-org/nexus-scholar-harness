---
workspace_id: SCI-000910
doi: 10.1016/j.dib.2022.108575
title: 'CoFly-WeedDB: A UAV image dataset for weed detection and species identification.'
authors:
- family_name: Krestenitis
  given_name: Marios
  orcid: null
- family_name: Raptis
  given_name: Emmanuel K
  orcid: null
- family_name: Kapoutsis
  given_name: Athanasios Ch
  orcid: null
- family_name: Ioannidis
  given_name: Konstantinos
  orcid: null
- family_name: Kosmatopoulos
  given_name: Elias B
  orcid: null
- family_name: Vrochidis
  given_name: Stefanos
  orcid: null
- family_name: Kompatsiaris
  given_name: Ioannis
  orcid: null
year: 2022
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:21:23.694893+00:00'
---

# CoFly-WeedDB: A UAV image dataset for weed detection and species identification.

Data in Brief 45 (2022) 108575

Contents lists available at ScienceDirect

Data in Brief

journal homepage: www.elsevier.com/locate/dib

Data Article

CoFly-WeedDB: A UAV image dataset for weed  detection and species identiﬁcation

Marios Krestenitis a , ∗, Emmanuel K. Raptis a , b ,  Athanasios Ch. Kapoutsis a , Konstantinos Ioannidis a ,  Elias B. Kosmatopoulos a , b , Stefanos Vrochidis a ,  Ioannis Kompatsiaris a

a Information Technologies Institute, The Centre for Research and Technology, Hellas, Thessaloniki 57001, Greece  b Department of Electrical and Computer Engineering, Democritus University of Thrace, Xanthi 67100, Greece

a b s t r a c t

a r t i c l e  i n f o

The CoFly-WeedDB contains 201 RGB images ( ∼436 MB)  from the attached camera of DJI Phantom Pro 4 from a cot-  ton ﬁeld in Larissa, Greece during the ﬁrst stages of plant  growth. The 1280 × 720 RGB images were collected while  the Unmanned Aerial Vehicle (UAV) was performing a cover-  age mission over the ﬁeld’s area. During the designed mis-  sion, the camera angle was adjusted to –87 °, vertically with  the ﬁeld. The ﬂight altitude and speed of the UAV were equal  to 5 m and 3 m/s, respectively, aiming to provide a close and  clear view of the weed instances. All images have been an-  notated by expert agronomists using the LabelMe annotation  tool, providing the exact boundaries of 3 types of common  weeds in this type of crop, namely (i) Johnson grass, (ii) Field  bindweed, and (iii) Purslane. The dataset can be used alone  and in combination with other datasets to develop AI-based  methodologies for automatic weed segmentation and classi-  ﬁcation purposes.

Article history:  Received 23 June 2022  Revised 28 July 2022  Accepted 29 August 2022  Available online 5 September 2022

Dataset link: CoFly-WeedDB: A UAV image  dataset for weed detection and species  identiﬁcation (Original data)

Keywords:  Precision agriculture  UAV dataset  Weed detection  Deep convolutional neural networks  Semantic segmentation

© 2022 The Authors. Published by Elsevier Inc.  This is an open access article under the CC BY license

( http://creativecommons.org/licenses/by/4.0/ )

∗Corresponding author.

E-mail address: mikrestenitis@iti.gr (M. Krestenitis).

https://doi.org/10.1016/j.dib.2022.108575  2352-3409/© 2022 The Authors. Published by Elsevier Inc. This is an open access article under the CC BY license  ( http://creativecommons.org/licenses/by/4.0/ )

2  M. Krestenitis, E.K. Raptis and A.Ch. Kapoutsis et al. / Data in Brief 45 (2022) 108575

Speciﬁcations Table

Subject  Computer Science  Speciﬁc subject area  Artiﬁcial Intelligence, Computer Vision and Pattern Recognition  Type of data  RGB images  How the data were acquired  Unmanned Aerial Vehicle - DJI Phantom 4 Pro  RGB Camera - 1 ′′ CMOS Effective pixels: 20 M with FOV 84 ° 8.8 mm/24 mm  (35 mm format equivalent) f/2.8 - f/11 auto focus at 1 m - ∞  Data format  Raw  Analyzed  Description of data collection  The RGB images were collected while the UAV was performing a coverage  mission over the ﬁeld’s area. During the designed mission, the camera angle  was adjusted to -87 °, vertically with the ﬁeld. The ﬂight altitude and speed of  the UAV were equal to 5 m and 3 m/s, respectively, aiming to provide a close  and clear view of the weed instances.  Utilized path planning platforms:  Software: https://github.com/CoFly-Project/Waypoint-Trajectory-Planning  Android DJI Adaptor: https://github.com/CoFly-Project/waypointmission  Data source location  Kileler, 415 00, Thessalian Plain, Larissa, Greece  Latitude and longitude from the agricultural ﬁeld: [39.54164,22.64298  39.54032,22.64436 39.54183,22.64687 39.54305,22.64542]  Data accessibility  Repository name: CoFly-WeedDB  Direct URL to data: https://zenodo.org/record/6697343#.YrQpwHhByV4  DOI: 10.5281/zenodo.6697343  Database description:  https://github.com/CoFly-Project/CoFly-WeedDB/blob/main/README.md

Value of the Data

• Presented data is a signiﬁcant addition to the ﬁeld of weed datasets, where the currently  available are limited, especially in case of examining species of southern Europe.  • Data are valuable for computer scientists and electrical engineers conducting research or de-  veloping tools focused on precision agriculture.  • Collected data can be employed to train and evaluate AI-based methods for weed detection.  • Collected data can be utilized in general for computer vision approaches for object segmen-  tation and counting, image analysis, etc.


## 1. Data Description

In this paper, a custom-built dataset is provided, oriented for precision agriculture operations.  More speciﬁcally, data were collected during a UAV ﬂight mission over a cotton ﬁeld, leading to a  set of 201 RGB images. Weed instances depicted in the acquired images were annotated accord-  ingly by ﬁeld experts, forming four classes, namely Johnson grass, Purslane, Field bindweed and  Background. In Fig. 1 sample images from the developed dataset are provided, while in Table 1  a statistical analysis of the dataset classes is presented. The provided data can be utilized to


> **Table 1**

> Statistical analysis presenting the number of pixels and instances per class contained in the custom-built dataset. As 
instance is mentioned a group of neighbour pixels that belong in the same class.

Class  Pixels (106)  Instances

Background  175  -  Johnson grass  1.44  77  Purslane  0.27  21  Field bindweed  7.56  286

M. Krestenitis, E.K. Raptis and A.Ch. Kapoutsis et al. / Data in Brief 45 (2022) 108575  3

Fig. 1. Sample images of the deployed dataset, where the annotation mask is overlaid over the captured RGB image for  illustration purposes. Johnson grass is highlighted with red, purslane with blue and ﬁeld bindweed with yellow color.

train and evaluate weed detection methods, especially those based on semantic segmentation  approaches.


## 2. Experimental Design, Materials and Methods

2.1. Dataset Acquisition

For the data collection, an autonomous UAV-based navigation scheme ( Fig. 2 ) was deployed  to cover the agricultural ﬁeld completely, ensuring maximum possible eﬃciency in the mission

Fig. 2. Top view of the data source location. The black lines indicate the boundaries of the cotton ﬁeld while the green  lines illustrate the UAV’s coverage path for precision-based crop monitoring.

4  M. Krestenitis, E.K. Raptis and A.Ch. Kapoutsis et al. / Data in Brief 45 (2022) 108575

while taking into consideration any constraints that could affect the objective (geometry shape  of the ﬁeld) and the integrity of the UAV (No-ﬂy zones/obstacles, battery limitations, etc.). The  autopilot system is based on a Coverage Path Planning problem [1] , and it utilizes a Spanning  Tree algorithm [2] to provide safe and eﬃcient paths. The deployed UAV coverage path planning  software is publicly available and can be found at [3] .

For the image acquisition, a single commercial UAV (DJI Phantom 4 Pro) was used equipped  with a visible camera sensor capturing light in red, green, and blue bands. For the mission con-  trol and execution of the extracted waypoints from the auto-navigation algorithm to the UAV,  a custom and user-friendly interface based on the UAV’s handling capabilities have been im-  plemented while offering a simpliﬁed form of on-site commands [4] . Speciﬁcally, the android  application (hosted on a Xiaomi Mi Max 2) is used as a data transceiver between the auto-  matic navigation algorithm and the ﬂight control system, allowing the UAV to follow the opti-  mal path in order to cover an agricultural ﬁeld and collect data. Finally, a portable 4G router  (tp-link M7350) was used to handle wirelessly the connectivity and message routing between  the smartphone and the path planning interface.

2.2. Collected Data Analysis

The deployed data collection mission led to a set of 201 RGB images of size 1280 × 720  pixels. Acquired images depict cotton crop lines, where different types of weeds interfere  amongst the crop plants. The collected dataset was manually annotated by ﬁeld-experts ca-  pable of conﬁdently distinguishing weeds from cotton plants. Towards this direction, LabelMe  [5] annotation tool was utilized to label depicted weed instances with polygonal annotations.  Thus, every weed instance is labeled in detail with a polygon outline. The speciﬁc annota-  tion approach was preferred to other approaches (e.g., bounding box), aiming to create a ﬁne-  grained annotated dataset capable of being utilized for semantic segmentation tasks, where  crucial information regarding the shape and the location of the detected objects can be pro-  vided. Considering the dataset classes, three different classes were deﬁned, namely Johnson  grass, Purslane and Field bindweed, where different types of weeds are enclosed in each  class accordingly, while the rest of the image is labeled as Background. In Fig. 1 , a set of  sample images from the developed dataset is presented, where it can be noticed the ef-  ﬁciency of the selected labeling approach to derive detailed and tailored to the depicted  objects annotations. The deployed dataset is open-access and publicly available [6] to the  research community.

As illustrated in Fig. 1 , weed detection is a challenging task since weed clusters are cap-  tured in a wide variety of shapes, sizes, and types. Deploying a dataset that encloses the ma-  jority of existing cases is not an easy task and requires a heavy amount of workforce to col-  lect data from a wide range of ﬁelds and annotate them accordingly. Furthermore, one should  take into consideration that depicted weeds are usually capturing a small portion of the image,  due to their natural size, especially in cases where UAV imagery is employed. Table 1 presents  the number of pixels for background and weed classes, as well as the total number of weed  instances enclosed in the developed dataset per class. Notice that due to the complex nature  of the problem, the custom-built dataset is imbalanced, leading to a quite challenging detec-  tion task. Last but not least, the dataset, apart from the weed detection and identiﬁcation,  can be used for additional precision agriculture tasks, such as crop row detection [7] , yield  estimation [8] , etc.

Ethics Statement

Not applicable.

M. Krestenitis, E.K. Raptis and A.Ch. Kapoutsis et al. / Data in Brief 45 (2022) 108575  5

Declaration of Competing Interest

The authors declare that they have no known competing ﬁnancial interests or personal rela-  tionships that could have appeared to inﬂuence the work reported in this paper.

Data Availability

CoFly-WeedDB: A UAV image dataset for weed detection and species identiﬁcation (Original  data) (Zenobo).

CRediT Author Statement

Marios Krestenitis: Conceptualization, Data curation, Writing – original draft, Visualiza-  tion, Software; Emmanuel K. Raptis: Conceptualization, Writing – original draft, Software;  Athanasios Ch. Kapoutsis: Conceptualization, Supervision, Project administration, Writing – review & editing; Konstantinos Ioannidis: Supervision, Project administration; Elias B. Kos-  matopoulos: Resources, Supervision, Funding acquisition; Stefanos Vrochidis: Resources, Super-  vision, Funding acquisition; Ioannis Kompatsiaris: Resources, Funding acquisition.

Acknowledgments

This research has been ﬁnanced by 1) the European Regional Development Fund of the Eu-  ropean Union and Greek national funds through the Operational Program Competitiveness, En-  trepreneurship and Innovation, under the call RESEARCH - CREATE – INNOVATE, CoFly (project  code:T1EDK-00636) and 2) European Union’s Horizon 2020 Research and Innovation Programme,  TREEADS under Grant Agreement No 101036926.


## References

[1] E. Galceran, M. Carreras, A survey on coverage path planning for robotics, Robot. Auton. syst. 61 (12) (2013) 1258–

1276, doi: 10.1016/j.robot.2013.09.004 .  [2] Y. Gabriely, E. Rimon, Spanning-tree based coverage of continuous areas by a mobile robot, Ann. Math. Artif. Intell.

31 (1) (2001) 77–98, doi: 10.1023/A:1016610507833 .  [3] A waypoint-based mission planner for coverage and inspection tasks. https://github.com/CoFly-Project/

Waypoint-Trajectory-Planning , 2022 (accessed 21 July 2022).  [4] S.D. Apostolidis, P.C. Kapoutsis, A.C. Kapoutsis, E.B. Kosmatopoulos, Cooperative multi-UAV coverage mission planning

platform for remote sensing applications, Auton. Robots 46 (2) (2022) 373–400, doi: 10.1007/s10514- 021- 10028- 3 .  [5] Image polygonal annotation with python. https://github.com/wkentaro/labelme , 2022 (accessed 21 July 2022).  [6] CoFly-WeedDB dataset https://github.com/CoFly-Project/CoFly-WeedDB , 2022 (accessed 21 July 2022).  [7] G.D. Karatzinis, S.D. Apostolidis, A.C. Kapoutsis, L. Panagiotopoulou, Y.S. Boutalis, E.B. Kosmatopoulos, Towards an

integrated low-cost agricultural monitoring system with unmanned aircraft system, in: Proceedings of the Interna-  tional Conference on Unmanned Aircraft Systems (ICUAS), IEEE, 2020, pp. 1131–1138, doi: 10.1109/ICUAS48674.2020.  9213900 .  [8] Y. Huang, H.J. Brand, R. Sui, S.J. Thomson, T. Furukawa, M.W. Ebelhar, Cotton yield estimation using very high-

resolution digital images acquired with a low-cost small unmanned aerial vehicle, Trans. ASABE 59 (6) (2016) 1563– 1574, doi: 10.13031/trans.59.11831 .
