---
workspace_id: SCI-001406
doi: 10.1109/ingarss51564.2021.9792009
title: Classification and Identification of Crops Using Deep Learning with UAV Data
authors:
- family_name: Narvaria
  given_name: A.
  orcid: null
- family_name: Kumar
  given_name: U.
  orcid: null
- family_name: Jhanwwee
  given_name: Kanumuru Shree
  orcid: null
- family_name: Dasgupta
  given_name: A.
  orcid: null
- family_name: Kaur
  given_name: Gurdeep
  orcid: null
year: 2021
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:42.205566+00:00'
---

# Classification and Identification of Crops Using Deep Learning with UAV Data

CLASSIFICATION AND IDENTIFICATION OF CROPS USING DEEP LEARNING WITH

2021 IEEE International India Geoscience and Remote Sensing Symposium (InGARSS) | 978-1-6654-4249-7/21/$31.00 ©2021 IEEE | DOI: 10.1109/InGARSS51564.2021.9792009

UAV DATA

Abhishek Narvaria, Uttam Kumar, Senior Member, IEEE, Kanumuru Shree Jhanwwee,

Anindita Dasgupta, Member, IEEE and Gurdeep Jyoti Kaur

Spatial Computing Laboratory, Center for Data Sciences,  International Institute of Information Technology Bangalore (IIITB), Bangalore 560100, India.

Email: abhisheknarvaria@iiitb.ac.in, uttam@iiitb.ac.in, shree.jhanwwee@iiitb.ac.in,

anindita.dasgupta@iiitb.ac.in, gjyoti.kaur@gmail.com


## ABSTRACT

Agriculture is a source of livelihood for the majority of 
Indian population. The current agricultural problems 
include timely estimation of crop yield, detection of crop 
disease, and assessment of damages due to natural disasters 
such as flood, drought, etc. Any proposed solution to these 
problems will require accurate classification of crops. In 
this perspective, UAV (unmanned aerial vehicle) data are 
proving to be crucial in providing images of the land 
surface in multispectral channels such as blue (B), green 
(G), red (R), near infrared, red edge and long wave infrared 
thermal bands. Once the UAV images have been obtained, 
segmentation and classification of crops can be performed 
using deep learning techniques. The objectives of this work 
is to apply U-Net convolutional neural network (CNN) 
architecture to (i) find the best combination of input 
spectral bands for various crop classification such as wheat, 
cotton, maize, grass, and soil, (ii) to analyse the role of 
including vegetation indices (NDVI and EVI) in crop 
classification, and (iii) to analyse the role of textural 
parameters in performing semantic segmentation of the 
multiple crops in the scene. Average accuracy of the trained 
model was 83.35% with RGB bands and 74.61% with CIR 
(Colour Infrared) composite images. Results indicated that 
inclusion of NDVI in CIR input dataset yield high 
segmentation accuracy of 83.85% while dealing with the 
five classes’ separation problem. 
 
Index Terms—Crop classification, UAV (unmanned aerial 
vehicle), CNN, U-Net, NDVI, EVI, Haralick texture 
features

18% to the country’s GDP (gross domestic product). With  the large existing and increasing population, there is a  greater demand on the quantity, quality, high nutritious- value and variety of agricultural food products. The current  agricultural problems include automatic and timely  estimation of crop yield, detection of crop disease, and  assessment of damage due to natural disasters such as  flood, drought, etc. Any proposed solution to these  problems will require accurate classification of crops.  Advancements in computer vision techniques are being  widely used to segregate different types of crops, monitor  their health, assess soil quality, etc. with images acquired  from UAVs (unmanned aerial vehicles). UAV provide data  of the land surface in multispectral channels such as blue  (B), green (G), red (R), near infrared (NIR), red edge and  long wave infrared thermal bands. Once the UAV images  have been obtained, segmentation and classification of  crops can be performed using deep learning techniques  through automated processes, thereby reducing manual  efforts. Identification and segmentation of crops like maize,  cotton and different types of soil have been reported using  CNN (convolutional neural networks) [1] while analysing  the impact of climatic variables on the growth of vegetation  [2]. Methods to detect disease in plants using image  classification and segmentation [3] using 5000 pictures of  diseased and healthy plants [4] have also been explored.  Another study was conducted to analyse the usage of high  resolution space cameras with high definition images [5] to  recognise soybean leaf disease.     The objectives of this study is to apply U-Net convolutional  neural networks (CNN) architecture to (i) find the best  combination of input spectral bands for various crop  classification such as wheat, cotton, maize, grass, and soil,  (ii) to analyse the role of including spectral vegetation  indices such as NDVI (Normalized Difference Vegetation  Index) and EVI (Enhanced Vegetation Index) in crop  classification, and (iii) to analyse the role of textural  parameters such as angular second moment, contrast,


## 1. INTRODUCTION

Agriculture forms the backbone of Indian economy 
providing employment to half of the country’s population 
directly or indirectly. In 2018, agricultural sector employed 
more than 50% of the Indian workforce and contributed 17-

153 978-1-6654-4249-7/21/$31.00 ©2021 IEEE InGARSS 2021

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:46:59 UTC from IEEE Xplore.  Restrictions apply.

entropy and inverse difference moment to perform semantic  segmentation of the multiple crops. The study uses data  generated from multispectral camera attached to light  weight UAV. Various combinations of vegetation indices  and textural features were studied and tested with the aim  of maximising the accuracy of the model.

2.4. IDM - IDM (Inverse Difference Moment) is the  measure of local homogeneity, which reflects the clarity  and regularity of the texture. The texture is clear, regular,  easy to describe, and has a larger value. P(i,j) = element i, j  of the normalized symmetrical GLCM.

i j IDM i j                                (4)

2 P( , ) 1 ( ) i j


## 2. REVIEW OF SPECTRAL VEGETATION INDICES

AND TEXTURAL FEATURES

2.5.  ENTROPY  -  Entropy  (ENT)  measures  the  randomness of the amount of information contained in an  image and expresses the complexity of the image. P(i,j) =  element i, j of the normalized symmetrical GLCM. Entropy  ranges from 0 to infinite.

2.1. NDVI - NDVI (Normalized Difference Vegetation  Index) quantifies vegetation by measuring the difference  between NIR which is strongly reflected by vegetation and  RED light which is absorbed by vegetation. Chlorophyll  which is a health indicator, strongly absorbs visible light,  and the cellular structure of the leaves strongly reflect NIR.  When the plant is diseased, it absorbs more NIR light.  Therefore, observing the pattern of NIR and RED light  indicates the presence of chlorophyll and plant health.  NDVI value ranges from -1 to +1 where higher values  towards +1 indicates green vegetation, 0 indicates barren  land and bare soil, and lower values of NDVI (< -0.1)  corresponds to cloud, water, snow, etc.

i j ENT i j i j                        (5)

P( , )log P( , )

2.6. CONTRAST - CONTRAST (CON) reflects the  sharpness of the image and the depth of the grooves of the  texture. The sharper the texture, the greater the contrast.  P(i,j) = element i, j of the normalized symmetrical GLCM.

( ) ( ) NIR RED NDVI NIR RED   

i j CON i j i j                                      (6)

(1)

2 ( ) P( , )

2.2. EVI - EVI (Enhanced Vegetation Index) is used to  measure  the greenness of vegetation. Atmospheric  conditions and canopy background noise can also be  corrected by usage of EVI. EVI uses three values, namely L  for elimination of effects from canopy background, C as  coefficient for atmospheric resistance, and B for values  from the BLUE band. Background, atmospheric noise and  saturation can be eliminated in most cases by these  enhancements. The coefficients adopted in the MODIS-EVI  algorithm are L=1, C1 = 6, C2 = 7.5 and G (gain factor) =  2.5.


## 3. DATA AND METHODOLOGY

The data used in this study consisted of multispectral 
images 
of 
specific 
wavelength 
ranges 
in 
the 
electromagnetic 
spectrum 
(Table 
1) 
captured 
by 
Micasense® [6] Altum camera mounted on a UAV at 3 
mega pixel resolution. The images were acquired over a 
small agricultural field in Dharwad district, Karnataka, 
India on 21st and 22nd October, 14th November and 4th 
December 2019 (see Figure 1). The image pre-processing 
framework is shown in Figure 2 which involved reading 
metadata, converting raw images to radiance and radiance 
to reflectance, corrections for distorted images, image 
alignment, image enhancement, and finally RGB (Red-
Green-Blue) and CIR (Color Infrared) composite image 
generation from multispectral bands. Natural colour RGB 
composite images were obtained by combining red, green 
and blue bands and combination of red, green and NIR 
resulted in CIR composite images. 
 
Ground truth samples for each crop type were generated by 
labelling the pixels with the help of domain knowledge and 
other available ancillary information using open source 
image annotation tool - GNU Image Manipulation (GIMP).

( ) ( 1 2 ) NIR RED EVI G NIR C RED C BLUE L        

(2)

2.3. ASM - ASM (Angular Second Moment), also known  as energy, is a measure of the uniformity of the image gray  distribution and the thickness of the texture. P(i,j) =  element i, j of the normalized symmetrical Gray Level Co- occurrence Matrix (GLCM). ASM returns sum of squared  elements in GLCM and ranges from 0 to 1. A value of 1  indicates a constant image.

i j ASM i j                        (3)

2 P( , )

154

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:46:59 UTC from IEEE Xplore.  Restrictions apply.

Different classes like wheat, maize, cotton and grass, and  soil were identified and labelled with different intensity as  shown in Figure 3, which were then saved in gray scale.

is shown in Figure 4.


> **Table 1: UAV bands with centre wavelength and**

bandwidth  Band Name  Wavelength  Bandwidth  Blue  475 nm  32 nm  Green  560 nm  27 nm  Red  668 nm  14 nm  Red Edge  717 nm  12 nm  Near IR  842 nm  57 nm  Thermal  11 µm  6 µm


> **Figure 3: RGB images (top row) with corresponding**

ground truth (bottom row).


> **Figure 1: Sample raw images captured by the UAV at**

single instance showing six bands.


> **Figure 4: Flowchart of the overall methodology.**


## 4. RESULTS, DISCUSSION AND CONCLUSION

Five classes of interest namely, cotton, wheat, maize, grass 
and soil were classified with various combinations of 
spectral bands, vegetation indices and textural features such 
as RGB, RGB+NIR, RGB+NDVI, RGB+EVI, CIR, 
CIR+RGB+NIR, 
CIR+NDVI, 
CIR+EVI, 
RGB+ASM, 
RGB+IDM, RGB+ENT and RGB+CON using U-Net. 
Accuracy assessment revealed that CIR with NDVI gave 
most accurate results (83.85% average accuracy highlighted 
in bold in Table 3) for segregation of crops using U-Net 
model as shown in Tables 2, 3 and 4. Integration of spectral 
and textural features did not improve the model’s 
performance. Among various textural features, CON gave 
the highest average accuracy of 77.11%. Combination of 
EVI with RGB or CIR rendered poor results (~58.5-60% 
average accuracy). RGB with NIR band and CIR with NIR 
band showed least average accuracy (~37-47%) among all 
the band and spectral combinations. Predicted U-Net output 
from CIR+NDVI bands are shown in Figure 5.


> **Figure 2: Image pre-processing steps.**

> U-Net model has emerged as the primary tool for image 
segmentation that partitions the image into different 
segments, each representing a different class. The U-Net 
model was trained with pre-processed training images and 
their corresponding ground truth labels in Python 
programming language. This was repeated for all input 
spectral combinations like NDVI and EVI along with 
textural features like Entropy, ASM, etc. Performance 
evaluation of the model was done with unseen data sample 
for each experiment. Accuracy assessment was carried out 
by computing Jaccard index. Here, if the predicted value set 
is represented by ‘x’ and the real value set is represented by 
‘y’, then Jaccard score is the ratio of number of values that 
overlap in x and y to the number of values that do not 
overlap. True Accuracy was calculated with respect to 
ground truth. Flowchart depicting the overall methodology

155

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:46:59 UTC from IEEE Xplore.  Restrictions apply.

This study is a contribution to demonstrate the scope of  deep neural networks based semantic segmentation in  agricultural crop classification from multispectral UAV  data. Integration of thermal and Red edge bands along with  the other spectral bands will be explored in future for crop  segmentation.


> **Table 2: Accuracy assessment of RGB spectral band**

combinations  IMAGE  RGB  RGB+NIR  RGB+NDVI  RGB+EVI  Image-1  88.21  15.21  92.29  12.06  Image-2  66.21  66.12  28.16  57.18  Image-3  86.81  61.31  84.77  86.94  Image-4  84.52  62.94  82.76  87.36  Image-5  74.92  46.34  72.21  83.85  Image-6  99.43  31.27  99.98  32.34  Average  83.35  47.19  76.69  59.95


> **Table 3: Accuracy assessment of CIR spectral band**

combinations  IMAGE  CIR  CIR+RGB+NIR  CIR+NDVI  CIR+EVI  Image-1  91.36  46.93  94.24  50.19  Image-2  28.67  53.58  66.14  75.12  Image-3  84.19  30.27  84.77  79.41  Image-4  74.72  19.82  82.78  24.33  Image-5  70.88  49.57  75.21  86.49  Image-6  97.85  23.79  99.98  35.51  Average  74.61  37.32  83.85  58.50    Table 4: Accuracy assessment of RGB + textural feature


> **Figure 5: Results from CIR+NDVI with U-Net.**

> Classification of plant seedling images using deep learning, pages 
1839–1844, 2018. 
[2] 
Y. Guo, S. Chen, Z. Wu, S. Wang, C. R. Bryant, J. 
Senthilnath, M. Cunha, and Y. H. Fu. Integrating spectral and 
textural information for monitoring the growth of pear trees using 
optical images from the UAV platform. Remote Sensing, 13, 2021. 
[3] 
P. Panchal, V.C. Raman, and S. Mantri. In Proceedings 4th 
International Conference on Computational Systems and 
Information Technology for Sustainable Solution (CSITSS). Plant 
diseases detection and classification using machine learning 
models, volume 4, pages 1–6, 2019.  
[4] 
V. Suma, R. A. Shetty, R. F. Tated, S. Rohan, and T. S. 
Pujar. 
In Proceedings 
3rd 
International 
conference 
on 
Electronics, Communication and Aerospace Technology (ICECA). 
CNN 
based 
leaf 
disease 
identification 
and 
remedy 
recommendation system, pages 395–399, 2019. 
[5] 
G. K. Menezes, A. D. S. Oliveira, M. Alvarez, W. P. 
Amorim, N. A. D. S. Belete, G. G. Da Silva, E. C. Tetila, B. B. 
Machado and H. Pistori. Automatic recognition of soybean leaf 
diseases using UAV images and deep convolutional. Neural 
Networks, 28:903 – 907, 2020. 
[6] 
MicaSense, Inc. https://www.micasense.com, 2020. [Last 
accessed: 09th November 2021]

IMAGE  ASM  IDM  ENT  CON  Image-1  82.17  47.39  70.69  93.41  Image-2  25.99  83.88  68.94  29.56  Image-3  72.14  87.31  14.94  84.77  Image-4  60.22  63.32  15.45  82.73  Image-5  60.36  79.82  29.25  72.21  Image-6  85.29  46.17  3.33  99.99  Average  64.61  67.98  33.76  77.11

ACKNOWLEDGEMENT    We thank CSIR-4PI (Fourth Paradigm Institute), Bangalore  and University of Agricultural Sciences (UAS), Dharwad  for providing the UAV data. We are grateful to IIIT  Bangalore for the infrastructure support and acknowledge  Infosys Foundation for the financial assistance through the  Infosys Foundation Career Development Chair Professor.


## REFERENCES

[1] 
R.C. Alimboyong, A.A. Hernandez, and R.P. Medina. In 
Proceedings TENCON 2018 - 2018 IEEE Region 10 Conference.

156

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:46:59 UTC from IEEE Xplore.  Restrictions apply.
